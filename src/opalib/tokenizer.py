"""
Tokenizer Module
Implements Byte Pair Encoding (BPE) tokenization
"""

import json
import re
from typing import List, Dict, Tuple, Set
from collections import defaultdict


class BPETokenizer:
    """Byte Pair Encoding tokenizer for converting text to tokens."""
    
    def __init__(self, vocab_size: int = 50000):
        """
        Initialize BPE tokenizer.
        
        Args:
            vocab_size: Maximum vocabulary size.
        """
        self.vocab_size = vocab_size
        self.word_tokenizer = re.compile(r"\w+|[^\w\s]")
        self.vocab = {}
        self.merges = []
        self.token_to_id = {}
        self.id_to_token = {}
        self._initialize_vocab()
    
    def _initialize_vocab(self):
        """Initialize basic vocabulary with bytes."""
        # Start with all single bytes
        for i in range(256):
            self.token_to_id[bytes([i]).decode('latin1')] = i
            self.id_to_token[i] = bytes([i]).decode('latin1')
        self.vocab = dict(self.token_to_id)
    
    def encode(self, text: str) -> List[int]:
        """
        Encode text to token IDs.
        
        Args:
            text: Input text to encode.
        
        Returns:
            List of token IDs.
        """
        # Normalize text
        text = text.lower()
        words = self.word_tokenizer.findall(text)
        
        tokens = []
        for word in words:
            # Convert word to byte representation
            word_tokens = list(word.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))
            
            # Apply BPE merges
            word_tokens = self._apply_bpe(word_tokens)
            
            # Convert to IDs
            for token in word_tokens:
                if token in self.token_to_id:
                    tokens.append(self.token_to_id[token])
                else:
                    # Unknown token - use special token
                    tokens.append(0)
        
        return tokens
    
    def decode(self, token_ids: List[int]) -> str:
        """
        Decode token IDs back to text.
        
        Args:
            token_ids: List of token IDs.
        
        Returns:
            Decoded text.
        """
        tokens = []
        for token_id in token_ids:
            if token_id in self.id_to_token:
                tokens.append(self.id_to_token[token_id])
            else:
                tokens.append("[UNK]")
        
        return "".join(tokens)
    
    def _apply_bpe(self, tokens: List[str]) -> List[str]:
        """Apply learned BPE merges to tokens."""
        for merge in self.merges:
            i = 0
            while i < len(tokens) - 1:
                if tokens[i] + tokens[i + 1] == merge:
                    tokens = tokens[:i] + [merge] + tokens[i + 2:]
                else:
                    i += 1
        return tokens
    
    def train(self, texts: List[str], num_merges: int = 1000):
        """
        Train tokenizer on texts.
        
        Args:
            texts: List of texts to train on.
            num_merges: Number of BPE merge operations.
        """
        # Create initial word frequencies
        word_freqs = defaultdict(int)
        
        for text in texts:
            words = self.word_tokenizer.findall(text.lower())
            for word in words:
                word_freqs[word] += 1
        
        # Perform BPE merges
        for _ in range(num_merges):
            pairs = self._get_pair_frequencies(word_freqs)
            if not pairs:
                break
            
            best_pair = max(pairs, key=pairs.get)
            word_freqs = self._merge_pair(word_freqs, best_pair)
            self.merges.append("".join(best_pair))
            
            # Add merged token to vocabulary
            merged_token = "".join(best_pair)
            next_id = len(self.token_to_id)
            self.token_to_id[merged_token] = next_id
            self.id_to_token[next_id] = merged_token
    
    def _get_pair_frequencies(self, word_freqs: Dict) -> Dict[Tuple[str, str], int]:
        """Get frequency of adjacent token pairs."""
        pairs = defaultdict(int)
        
        for word, freq in word_freqs.items():
            symbols = list(word)
            for i in range(len(symbols) - 1):
                pairs[tuple([symbols[i], symbols[i + 1]])] += freq
        
        return pairs
    
    def _merge_pair(self, word_freqs: Dict, pair: Tuple[str, str]) -> Dict:
        """Merge all occurrences of a pair."""
        new_word_freqs = {}
        bigram = "".join(pair)
        replacement = bigram
        
        for word, freq in word_freqs.items():
            new_word = word.replace("".join(pair), replacement)
            new_word_freqs[new_word] = freq
        
        return new_word_freqs
    
    def save(self, filepath: str):
        """Save tokenizer to file."""
        data = {
            "token_to_id": self.token_to_id,
            "id_to_token": {str(k): v for k, v in self.id_to_token.items()},
            "merges": self.merges,
            "vocab_size": self.vocab_size
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)
    
    def load(self, filepath: str):
        """Load tokenizer from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.token_to_id = data["token_to_id"]
        self.id_to_token = {int(k): v for k, v in data["id_to_token"].items()}
        self.merges = data["merges"]
        self.vocab_size = data["vocab_size"]


class SimpleTokenizer:
    """Simple word-based tokenizer for quick use."""
    
    def __init__(self):
        self.word_to_id = {}
        self.id_to_word = {}
        self.word_count = 0
    
    def encode(self, text: str) -> List[int]:
        """Convert text to token IDs."""
        words = text.lower().split()
        tokens = []
        
        for word in words:
            if word not in self.word_to_id:
                self.word_to_id[word] = self.word_count
                self.id_to_word[self.word_count] = word
                self.word_count += 1
            
            tokens.append(self.word_to_id[word])
        
        return tokens
    
    def decode(self, token_ids: List[int]) -> str:
        """Convert token IDs back to text."""
        words = [self.id_to_word.get(tid, "[UNK]") for tid in token_ids]
        return " ".join(words)
