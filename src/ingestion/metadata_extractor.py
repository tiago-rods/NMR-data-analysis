import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExperimentMetadata:
    id_experimento: str
    fabricante: str
    frequencia: float
    biofluido: str
    ferramenta: str
    tecnologia: str
    tamanho: int

class MetadataExtractor:
    """
    Extracts metadata from standardized (but occasionally permuted) NMR CSV filenames.
    Follows SOLID principles: 
    - Single Responsibility: Only responsible for parsing filename metadata.
    - Open/Closed: Easy to extend known tokens without changing the core regex logic.
    """
    KNOWN_BIOFLUIDS = {'Soro', 'Urina', 'Plasma'}
    KNOWN_TOOLS = {'nmRanalysis', 'ASICS', 'MagMet', 'Batman'}
    
    @classmethod
    def extract(cls, filepath: str | Path) -> Optional[ExperimentMetadata]:
        """
        Parses the filename to extract metadata like experiment ID, frequency, tool, etc.
        """
        filename = Path(filepath).name
        
        # Regular expressions for explicit patterns
        id_match = re.search(r'(LNBio\d+)', filename, re.IGNORECASE)
        freq_match = re.search(r'(\d+)MHz', filename, re.IGNORECASE)
        size_match = re.search(r'size(\d+)', filename, re.IGNORECASE)
        
        if not id_match or not freq_match or not size_match:
            return None
            
        # Split by underscore to find standard categorical tags
        parts = set(filename.replace('.csv', '').replace('quantificationcsv', '').replace('quantification', '').split('_'))
        
        biofluido = next((p for p in parts if p in cls.KNOWN_BIOFLUIDS), 'Unknown')
        ferramenta = next((p for p in parts if p in cls.KNOWN_TOOLS), 'Unknown')
        
        # Infer Manufacturer
        fabricante = 'Unknown'
        if 'Agilent' in parts: 
            fabricante = 'Agilent'
        elif 'Bruker' in parts: 
            fabricante = 'Bruker'
        
        # Infer Technology (File input format)
        tecnologia = 'csv' if 'csv' in parts else 'fid' if 'fid' in parts else 'Unknown'

        return ExperimentMetadata(
            id_experimento=id_match.group(1),
            fabricante=fabricante,
            frequencia=float(freq_match.group(1)),
            biofluido=biofluido,
            ferramenta=ferramenta,
            tecnologia=tecnologia,
            tamanho=int(size_match.group(1))
        )
