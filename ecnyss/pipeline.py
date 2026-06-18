"""Pipeline module for ecnyss - composing existing modules for data processing.

This module provides a higher-order capability by integrating:
- hash_chain: for cryptographic hash chain creation and verification
- provenance: for ProvenanceRecord creation and management
- encoding: for data encoding/decoding
- identifiers: for unique ID generation
- functional: for functional composition utilities
"""
from __future__ import annotations

import time
from typing import Any

from ecnyss.hash_chain import HashChain
from ecnyss.provenance import ProvenanceRecord
from ecnyss.encoding import encode_bytes, decode_bytes
from ecnyss.identifiers import generate_id
from ecnyss.functional import compose


def _create_data_dict(input_data: bytes) -> dict[str, Any]:
    """Create a data dictionary from input bytes.
    
    Encodes the bytes and creates a structured data dict with metadata.
    """
    encoded = encode_bytes(input_data)
    return {
        "id": generate_id(),
        "raw_length": len(input_data),
        "encoded": encoded,
        "checksum": hashlib_sha256(input_data),
    }


def hashlib_sha256(data: bytes) -> str:
    """Compute SHA256 hash of data."""
    import hashlib
    return hashlib.sha256(data).hexdigest()


def _create_hash_chain(input_data: bytes) -> HashChain:
    """Create a hash chain from input data."""
    chain = HashChain()
    # Add the input data hash as the first link
    data_hash = hashlib_sha256(input_data)
    chain.add(data_hash)
    return chain


def run(input_data: bytes) -> ProvenanceRecord:
    """Run the pipeline on input bytes.
    
    Args:
        input_data: Raw bytes to process.
        
    Returns:
        ProvenanceRecord with data, chain, timestamp, and metadata.
    """
    data_dict = _create_data_dict(input_data)
    chain = _create_hash_chain(input_data)
    timestamp = time.time()
    
    return ProvenanceRecord(
        data=data_dict,
        chain=chain,
        timestamp=timestamp,
        metadata=None,
    )


def run_with_metadata(input_data: bytes, metadata: dict[str, Any] | None) -> ProvenanceRecord:
    """Run the pipeline with custom metadata.
    
    Args:
        input_data: Raw bytes to process.
        metadata: Optional metadata dict to include in the record.
        
    Returns:
        ProvenanceRecord with data, chain, timestamp, and merged metadata.
    """
    base_record = run(input_data)
    
    if metadata is None:
        return base_record
    
    # Merge metadata with any existing metadata
    if base_record.metadata is None:
        merged_metadata = dict(metadata)
    else:
        merged_metadata = {**base_record.metadata, **metadata}
    
    return ProvenanceRecord(
        data=base_record.data,
        chain=base_record.chain,
        timestamp=base_record.timestamp,
        metadata=merged_metadata,
    )


def batch_run(inputs: list[bytes]) -> list[ProvenanceRecord]:
    """Run the pipeline on multiple inputs.
    
    Args:
        inputs: List of byte sequences to process.
        
    Returns:
        List of ProvenanceRecord objects, one per input.
    """
    return [run(input_data) for input_data in inputs]


def verify_chain(records: list[ProvenanceRecord]) -> bool:
    """Verify hash chain integrity for a list of records.
    
    Args:
        records: List of ProvenanceRecord objects to verify.
        
    Returns:
        True if all chains are valid, False otherwise.
    """
    if not records:
        return True
    
    for record in records:
        if record.chain is None:
            return False
        if not record.chain.verify():
            return False
    
    return True


# Composed pipeline function using functional composition
def create_pipeline(*processors: callable) -> callable:
    """Create a composed pipeline from multiple processor functions.
    
    Args:
        *processors: Variable number of processor functions to compose.
        
    Returns:
        A composed function that applies all processors in sequence.
    """
    return compose(*processors)


def process_with_chain(input_data: bytes, chain: HashChain | None = None) -> ProvenanceRecord:
    """Process data with an existing or new hash chain.
    
    Args:
        input_data: Raw bytes to process.
        chain: Optional existing HashChain to extend.
        
    Returns:
        ProvenanceRecord with the processed data and chain.
    """
    data_dict = _create_data_dict(input_data)
    
    if chain is None:
        chain = _create_hash_chain(input_data)
    else:
        # Extend existing chain with new data hash
        data_hash = hashlib_sha256(input_data)
        chain.add(data_hash)
    
    return ProvenanceRecord(
        data=data_dict,
        chain=chain,
        timestamp=time.time(),
        metadata=None,
    )
