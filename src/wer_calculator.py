import re
import logging
from typing import Dict, List, Tuple
from jiwer import wer, cer, compute_measures
import string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WERCalculator:
    def __init__(self):
        self.normalization_options = {
            'lowercase': True,
            'remove_punctuation': True,
            'remove_multiple_spaces': True,
            'strip': True,
            'remove_special_chars': True
        }
    
    def normalize_text(self, text: str, options: Dict[str, bool] = None) -> str:
        """
        Normalize text for WER calculation.
        
        Args:
            text: Input text to normalize
            options: Normalization options dictionary
        
        Returns:
            Normalized text
        """
        if options is None:
            options = self.normalization_options
        
        normalized = text
        
        if options.get('lowercase', True):
            normalized = normalized.lower()
        
        if options.get('remove_punctuation', True):
            translator = str.maketrans('', '', string.punctuation)
            normalized = normalized.translate(translator)
        
        if options.get('remove_special_chars', True):
            normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        if options.get('remove_multiple_spaces', True):
            normalized = re.sub(r'\s+', ' ', normalized)
        
        if options.get('strip', True):
            normalized = normalized.strip()
        
        return normalized
    
    def calculate_wer(self, reference: str, hypothesis: str, normalize: bool = True) -> Dict[str, float]:
        """
        Calculate Word Error Rate and related metrics.
        
        Args:
            reference: Ground truth text
            hypothesis: Predicted text from ASR
            normalize: Whether to normalize texts before calculation
        
        Returns:
            Dictionary with WER, CER, and other metrics
        """
        if normalize:
            reference = self.normalize_text(reference)
            hypothesis = self.normalize_text(hypothesis)
        
        measures = compute_measures(reference, hypothesis)
        
        metrics = {
            'wer': measures['wer'],
            'cer': measures['cer'],
            'hits': measures['hits'],
            'substitutions': measures['substitutions'],
            'deletions': measures['deletions'],
            'insertions': measures['insertions'],
            'reference_length': len(reference.split()),
            'hypothesis_length': len(hypothesis.split())
        }
        
        if metrics['reference_length'] > 0:
            metrics['accuracy'] = metrics['hits'] / metrics['reference_length']
        else:
            metrics['accuracy'] = 0.0
        
        return metrics
    
    def calculate_batch_wer(self, references: List[str], hypotheses: List[str], normalize: bool = True) -> Dict[str, float]:
        """
        Calculate WER for a batch of reference-hypothesis pairs.
        
        Args:
            references: List of ground truth texts
            hypotheses: List of predicted texts
            normalize: Whether to normalize texts
        
        Returns:
            Aggregated metrics dictionary
        """
        if len(references) != len(hypotheses):
            raise ValueError("Number of references and hypotheses must match")
        
        if normalize:
            references = [self.normalize_text(ref) for ref in references]
            hypotheses = [self.normalize_text(hyp) for hyp in hypotheses]
        
        overall_wer = wer(references, hypotheses)
        overall_cer = cer(references, hypotheses)
        
        individual_metrics = []
        for ref, hyp in zip(references, hypotheses):
            metrics = self.calculate_wer(ref, hyp, normalize=False)
            individual_metrics.append(metrics)
        
        avg_metrics = {
            'overall_wer': overall_wer,
            'overall_cer': overall_cer,
            'avg_wer': sum(m['wer'] for m in individual_metrics) / len(individual_metrics),
            'avg_cer': sum(m['cer'] for m in individual_metrics) / len(individual_metrics),
            'total_words': sum(m['reference_length'] for m in individual_metrics),
            'individual_metrics': individual_metrics
        }
        
        return avg_metrics
    
    def get_error_analysis(self, reference: str, hypothesis: str, normalize: bool = True) -> Dict[str, List[Tuple[str, str]]]:
        """
        Get detailed error analysis showing specific substitutions, deletions, and insertions.
        
        Args:
            reference: Ground truth text
            hypothesis: Predicted text
            normalize: Whether to normalize texts
        
        Returns:
            Dictionary with lists of errors by type
        """
        if normalize:
            reference = self.normalize_text(reference)
            hypothesis = self.normalize_text(hypothesis)
        
        ref_words = reference.split()
        hyp_words = hypothesis.split()
        
        from difflib import SequenceMatcher
        matcher = SequenceMatcher(None, ref_words, hyp_words)
        
        errors = {
            'substitutions': [],
            'deletions': [],
            'insertions': []
        }
        
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == 'replace':
                for i, j in zip(range(i1, i2), range(j1, j2)):
                    errors['substitutions'].append((ref_words[i], hyp_words[j]))
            elif op == 'delete':
                for i in range(i1, i2):
                    errors['deletions'].append(ref_words[i])
            elif op == 'insert':
                for j in range(j1, j2):
                    errors['insertions'].append(hyp_words[j])
        
        return errors