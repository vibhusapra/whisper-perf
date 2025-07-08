#!/usr/bin/env python3
import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

from src.config import Config
from src.audio_processor import AudioProcessor
from src.transcriber import GPT4OTranscriber
from src.wer_calculator import WERCalculator
from src.dataset_manager import DatasetManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GPT4OPerformanceTester:
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.transcriber = GPT4OTranscriber()
        self.wer_calculator = WERCalculator()
        self.dataset_manager = DatasetManager()
        
        self.results_dir = Config.RESULTS_DIR
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def run_single_test(self, audio_path: str, reference_text: str, speed_factor: float) -> Dict:
        """Run a single transcription test at specified speed."""
        logger.info(f"Testing {Path(audio_path).name} at {speed_factor}x speed")
        
        try:
            original_duration, original_size = self.audio_processor.get_audio_info(audio_path)
            
            if speed_factor == 1.0:
                processed_path = audio_path
            else:
                processed_path = self.audio_processor.process_audio(audio_path, speed_factor)
            
            processed_duration, processed_size = self.audio_processor.get_audio_info(processed_path)
            
            transcription, metadata = self.transcriber.transcribe(processed_path)
            
            wer_metrics = self.wer_calculator.calculate_wer(reference_text, transcription)
            
            # Get actual costs from metadata (token-based pricing)
            actual_cost = metadata.get('total_cost', 0)
            
            # Estimate what original would have cost
            original_file_size_mb = original_size / (1024 * 1024)
            original_cost = self.transcriber.estimate_cost(original_file_size_mb)
            
            result = {
                'file_name': Path(audio_path).name,
                'speed_factor': speed_factor,
                'original_duration': original_duration,
                'processed_duration': processed_duration,
                'duration_reduction': (1 - processed_duration/original_duration) * 100,
                'original_cost': original_cost,
                'actual_cost': actual_cost,
                'cost_savings': (1 - actual_cost/original_cost) * 100 if original_cost > 0 else 0,
                'processing_time': metadata['processing_time'],
                **wer_metrics,
                'input_tokens': metadata.get('input_tokens', 0),
                'output_tokens': metadata.get('output_tokens', 0),
                'total_tokens': metadata.get('total_tokens', 0),
                'transcription': transcription,
                'reference': reference_text
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in test: {str(e)}")
            return {
                'file_name': Path(audio_path).name,
                'speed_factor': speed_factor,
                'error': str(e)
            }
    
    def run_full_test(self, speed_factors: List[float] = None) -> pd.DataFrame:
        """Run complete test suite across all files and speed factors."""
        if speed_factors is None:
            speed_factors = Config.SPEED_FACTORS
        
        is_valid, issues = self.dataset_manager.validate_dataset()
        if not is_valid:
            logger.error("Dataset validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            sys.exit(1)
        
        dataset_items = self.dataset_manager.get_dataset_items()
        logger.info(f"Running tests on {len(dataset_items)} files with speeds: {speed_factors}")
        
        results = []
        total_tests = len(dataset_items) * len(speed_factors)
        
        with tqdm(total=total_tests, desc="Running tests") as pbar:
            for item in dataset_items:
                reference_text = self.dataset_manager.load_transcript(item['transcript_path'])
                
                for speed_factor in speed_factors:
                    result = self.run_single_test(
                        item['audio_path'],
                        reference_text,
                        speed_factor
                    )
                    results.append(result)
                    pbar.update(1)
        
        self.audio_processor.cleanup_temp_files()
        
        df = pd.DataFrame(results)
        return df
    
    def save_results(self, df: pd.DataFrame):
        """Save test results to CSV and JSON."""
        csv_path = os.path.join(self.results_dir, f"test_results_{self.timestamp}.csv")
        json_path = os.path.join(self.results_dir, f"test_results_{self.timestamp}.json")
        
        df.to_csv(csv_path, index=False)
        df.to_json(json_path, orient='records', indent=2)
        
        logger.info(f"Results saved to {csv_path} and {json_path}")
        return csv_path
    
    def generate_visualizations(self, df: pd.DataFrame):
        """Generate performance visualization plots."""
        plt.style.use('default')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        clean_df = df[~df['wer'].isna()].copy()
        
        ax = axes[0, 0]
        speed_wer = clean_df.groupby('speed_factor')['wer'].agg(['mean', 'std']).reset_index()
        ax.bar(speed_wer['speed_factor'], speed_wer['mean'], yerr=speed_wer['std'], capsize=5)
        ax.set_xlabel('Speed Factor')
        ax.set_ylabel('Word Error Rate (WER)')
        ax.set_title('Average WER by Speed Factor')
        ax.set_ylim(0, max(0.5, speed_wer['mean'].max() * 1.2))
        
        ax = axes[0, 1]
        speed_cost = clean_df.groupby('speed_factor')['cost_savings'].mean().reset_index()
        ax.bar(speed_cost['speed_factor'], speed_cost['cost_savings'])
        ax.set_xlabel('Speed Factor')
        ax.set_ylabel('Cost Savings (%)')
        ax.set_title('Average Cost Savings by Speed Factor')
        
        ax = axes[1, 0]
        for speed in clean_df['speed_factor'].unique():
            speed_data = clean_df[clean_df['speed_factor'] == speed]
            ax.scatter(speed_data['original_duration']/60, speed_data['wer'], 
                      label=f'{speed}x', alpha=0.7, s=100)
        ax.set_xlabel('Original Duration (minutes)')
        ax.set_ylabel('Word Error Rate (WER)')
        ax.set_title('WER vs Audio Duration')
        ax.legend()
        
        ax = axes[1, 1]
        metrics_df = clean_df.groupby('speed_factor').agg({
            'wer': 'mean',
            'cost_savings': 'mean',
            'processing_time': 'mean'
        }).round(3)
        
        ax.axis('tight')
        ax.axis('off')
        table = ax.table(cellText=metrics_df.values,
                        colLabels=['Avg WER', 'Avg Cost Savings %', 'Avg Process Time (s)'],
                        rowLabels=[f'{x}x' for x in metrics_df.index],
                        cellLoc='center',
                        loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        ax.set_title('Summary Statistics by Speed Factor', pad=20)
        
        plt.tight_layout()
        plot_path = os.path.join(self.results_dir, f"performance_analysis_{self.timestamp}.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualizations saved to {plot_path}")
        return plot_path
    
    def generate_report(self, df: pd.DataFrame):
        """Generate a comprehensive markdown report."""
        clean_df = df[~df['wer'].isna()].copy()
        
        report = f"""# GPT-4o Audio Performance Test Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Test Configuration
- **Files Tested**: {len(clean_df['file_name'].unique())}
- **Speed Factors**: {sorted(clean_df['speed_factor'].unique())}
- **Total Tests**: {len(clean_df)}

## Summary Results

| Speed Factor | Avg WER | Avg Cost ($) | Avg Input Tokens | Avg Output Tokens | Duration Reduction |
|--------------|---------|--------------|------------------|-------------------|---------------------|
"""
        
        for speed in sorted(clean_df['speed_factor'].unique()):
            speed_data = clean_df[clean_df['speed_factor'] == speed]
            avg_wer = speed_data['wer'].mean()
            avg_cost = speed_data['actual_cost'].mean()
            avg_input_tokens = speed_data['input_tokens'].mean()
            avg_output_tokens = speed_data['output_tokens'].mean()
            avg_duration_reduction = speed_data['duration_reduction'].mean()
            
            report += f"| {speed}x | {avg_wer:.3f} | ${avg_cost:.4f} | {avg_input_tokens:,.0f} | {avg_output_tokens:,.0f} | {avg_duration_reduction:.1f}% |\n"
        
        report += f"""
## Recommendations

Based on the test results:
"""
        
        best_speed = clean_df.groupby('speed_factor').agg({
            'wer': 'mean',
            'cost_savings': 'mean'
        })
        
        acceptable_wer_threshold = 0.15
        good_speeds = best_speed[best_speed['wer'] < acceptable_wer_threshold]
        
        if not good_speeds.empty:
            optimal_speed = good_speeds['cost_savings'].idxmax()
            report += f"""
- **Recommended Speed**: {optimal_speed}x
- **Expected WER**: {best_speed.loc[optimal_speed, 'wer']:.3f}
- **Expected Cost Savings**: {best_speed.loc[optimal_speed, 'cost_savings']:.1f}%
"""
        else:
            report += "\n- All tested speeds resulted in WER above acceptable threshold (15%)\n"
        
        report += """
## Detailed Results by File

"""
        
        for file_name in clean_df['file_name'].unique():
            file_data = clean_df[clean_df['file_name'] == file_name]
            report += f"### {file_name}\n\n"
            report += "| Speed | WER | Cost Savings | Processing Time |\n"
            report += "|-------|-----|--------------|----------------|\n"
            
            for _, row in file_data.iterrows():
                report += f"| {row['speed_factor']}x | {row['wer']:.3f} | {row['cost_savings']:.1f}% | {row['processing_time']:.2f}s |\n"
            
            report += "\n"
        
        report_path = os.path.join(self.results_dir, f"test_report_{self.timestamp}.md")
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Report saved to {report_path}")
        return report_path


def main():
    parser = argparse.ArgumentParser(description='Test GPT-4o audio performance at different playback speeds')
    parser.add_argument('--speeds', nargs='+', type=float, default=None,
                       help='Speed factors to test (default: 1.0, 2.0, 3.0)')
    parser.add_argument('--single-file', type=str, help='Test a single file only')
    parser.add_argument('--no-viz', action='store_true', help='Skip visualization generation')
    
    args = parser.parse_args()
    
    tester = GPT4OPerformanceTester()
    
    if args.single_file:
        logger.error("Single file testing not implemented yet")
        sys.exit(1)
    
    logger.info("Starting GPT-4o audio performance tests...")
    df = tester.run_full_test(speed_factors=args.speeds)
    
    if df.empty:
        logger.error("No test results generated")
        sys.exit(1)
    
    csv_path = tester.save_results(df)
    
    if not args.no_viz and not df[~df['wer'].isna()].empty:
        plot_path = tester.generate_visualizations(df)
    
    report_path = tester.generate_report(df)
    
    logger.info("Test completed successfully!")
    logger.info(f"Results: {csv_path}")
    logger.info(f"Report: {report_path}")


if __name__ == "__main__":
    main()