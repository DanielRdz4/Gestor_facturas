"""Módulo para la gestión y parseo de archivos XML de CFDIs (SAT México)."""

import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .mod_rutas import DIR_PENDIENTES, DIR_PROCESADAS

# Namespaces oficiales del SAT para CFDIs
CFDI_NAMESPACES = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'cfdi3': 'http://www.sat.gob.mx/cfd/3',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

@dataclass
class CFDIData:
    """Clase para almacenar los datos extraídos de un CFDI."""
    folio: Optional[str] = None
    serie: Optional[str] = None
    fecha_emision: Optional[datetime] = None
    total: Optional[float] = None
    subtotal: Optional[float] = None
    moneda: Optional[str] = None
    
    # Datos del emisor
    emisor_rfc: Optional[str] = None
    emisor_nombre: Optional[str] = None
    emisor_regimen: Optional[str] = None
    
    # Datos del receptor
    receptor_rfc: Optional[str] = None
    receptor_nombre: Optional[str] = None
    
    # Datos del timbre fiscal
    uuid: Optional[str] = None
    fecha_timbrado: Optional[datetime] = None
    
    # Metadatos
    version: Optional[str] = None
    archivo_origen: Optional[str] = None
    
    def __str__(self):
        return f"CFDI {self.serie}-{self.folio} | {self.emisor_nombre} → {self.receptor_nombre} | ${self.total}"

class CFDIParser:
    """Parser para archivos XML de CFDIs del SAT."""
    
    def __init__(self):
        self.namespaces = CFDI_NAMESPACES
    
    def parsear_archivo(self, ruta_archivo: Path) -> Optional[CFDIData]:
        """
        Parsea un archivo XML de CFDI y extrae los datos principales.
        
        Args:
            ruta_archivo (Path): Ruta al archivo XML del CFDI
            
        Returns:
            CFDIData: Objeto con los datos extraídos o None si hay error
        """
        try:
            if not ruta_archivo.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {ruta_archivo}")
            
            tree = ET.parse(ruta_archivo)
            root = tree.getroot()
            
            # Detectar versión del CFDI
            version = self._detectar_version(root)
            
            if version == "4.0":
                return self._parsear_cfdi_v4(root, ruta_archivo)
            elif version == "3.3":
                return self._parsear_cfdi_v3(root, ruta_archivo)
            else:
                raise ValueError(f"Versión de CFDI no soportada: {version}")
                
        except Exception as e:
            print(f"Error al parsear CFDI {ruta_archivo}: {e}")
            return None
    
    def _detectar_version(self, root) -> str:
        """Detecta la versión del CFDI basándose en el namespace."""
        if root.tag.startswith('{http://www.sat.gob.mx/cfd/4}'):
            return "4.0"
        elif root.tag.startswith('{http://www.sat.gob.mx/cfd/3}'):
            return "3.3"
        else:
            # Fallback: buscar en el atributo version
            return root.get('Version', '3.3')
    
    def _parsear_cfdi_v4(self, root, archivo: Path) -> CFDIData:
        """Parsea un CFDI versión 4.0."""
        cfdi = CFDIData()
        cfdi.version = "4.0"
        cfdi.archivo_origen = str(archivo.name)
        
        # Datos del comprobante
        cfdi.folio = root.get('Folio')
        cfdi.serie = root.get('Serie')
        cfdi.total = self._convertir_a_float(root.get('Total'))
        cfdi.subtotal = self._convertir_a_float(root.get('SubTotal'))
        cfdi.moneda = root.get('Moneda', 'MXN')
        cfdi.fecha_emision = self._convertir_fecha(root.get('Fecha'))
        
        # Datos del emisor
        emisor = root.find('cfdi:Emisor', self.namespaces)
        if emisor is not None:
            cfdi.emisor_rfc = emisor.get('Rfc')
            cfdi.emisor_nombre = emisor.get('Nombre')
            cfdi.emisor_regimen = emisor.get('RegimenFiscal')
        
        # Datos del receptor
        receptor = root.find('cfdi:Receptor', self.namespaces)
        if receptor is not None:
            cfdi.receptor_rfc = receptor.get('Rfc')
            cfdi.receptor_nombre = receptor.get('Nombre')
        
        # Datos del timbre fiscal
        self._extraer_timbre_fiscal(root, cfdi)
        
        return cfdi
    
    def _parsear_cfdi_v3(self, root, archivo: Path) -> CFDIData:
        """Parsea un CFDI versión 3.3."""
        cfdi = CFDIData()
        cfdi.version = "3.3"
        cfdi.archivo_origen = str(archivo.name)
        
        # Usar namespace v3 para elementos
        ns = {'cfdi': 'http://www.sat.gob.mx/cfd/3'}
        
        # Datos del comprobante
        cfdi.folio = root.get('folio') or root.get('Folio')
        cfdi.serie = root.get('serie') or root.get('Serie')
        cfdi.total = self._convertir_a_float(root.get('total') or root.get('Total'))
        cfdi.subtotal = self._convertir_a_float(root.get('subTotal') or root.get('SubTotal'))
        cfdi.moneda = root.get('Moneda', 'MXN')
        cfdi.fecha_emision = self._convertir_fecha(root.get('fecha') or root.get('Fecha'))
        
        # Datos del emisor
        emisor = root.find('cfdi:Emisor', ns)
        if emisor is not None:
            cfdi.emisor_rfc = emisor.get('rfc') or emisor.get('Rfc')
            cfdi.emisor_nombre = emisor.get('nombre') or emisor.get('Nombre')
        
        # Datos del receptor
        receptor = root.find('cfdi:Receptor', ns)
        if receptor is not None:
            cfdi.receptor_rfc = receptor.get('rfc') or receptor.get('Rfc')
            cfdi.receptor_nombre = receptor.get('nombre') or receptor.get('Nombre')
        
        # Datos del timbre fiscal
        self._extraer_timbre_fiscal(root, cfdi)
        
        return cfdi
    
    def _extraer_timbre_fiscal(self, root, cfdi: CFDIData):
        """Extrae datos del timbre fiscal digital."""
        # Buscar el complemento de timbre fiscal
        complemento = root.find('.//tfd:TimbreFiscalDigital', self.namespaces)
        if complemento is not None:
            cfdi.uuid = complemento.get('UUID')
            cfdi.fecha_timbrado = self._convertir_fecha(complemento.get('FechaTimbrado'))
    
    def _convertir_fecha(self, fecha_str: str) -> Optional[datetime]:
        """Convierte string de fecha a objeto datetime."""
        if not fecha_str:
            return None
        
        # Formatos comunes de fecha en CFDIs
        formatos = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d'
        ]
        
        for formato in formatos:
            try:
                return datetime.strptime(fecha_str, formato)
            except ValueError:
                continue
        
        print(f"No se pudo convertir la fecha: {fecha_str}")
        return None
    
    def _convertir_a_float(self, valor: str) -> Optional[float]:
        """Convierte string a float de manera segura."""
        if not valor:
            return None
        try:
            return float(valor)
        except ValueError:
            return None

# Funciones de utilidad para usar desde otros módulos
def parsear_cfdi(archivo_path: Path) -> Optional[CFDIData]:
    """
    Función de conveniencia para parsear un CFDI.
    
    Args:
        archivo_path (Path): Ruta al archivo XML del CFDI
        
    Returns:
        CFDIData: Datos extraídos del CFDI o None si hay error
    """
    parser = CFDIParser()
    return parser.parsear_archivo(archivo_path)

def procesar_cfdis_pendientes() -> list[CFDIData]:
    """
    Procesa todos los archivos XML en el directorio de pendientes.
    
    Returns:
        list[CFDIData]: Lista con los datos de todos los CFDIs procesados
    """
    cfdis = []
    if DIR_PENDIENTES.exists():
        for archivo in DIR_PENDIENTES.glob("*.xml"):
            cfdi_data = parsear_cfdi(archivo)
            if cfdi_data:
                cfdis.append(cfdi_data)
    return cfdis

def obtener_resumen_cfdi(cfdi_data: CFDIData) -> Dict[str, Any]:
    """
    Obtiene un resumen de los datos principales de un CFDI.
    
    Args:
        cfdi_data (CFDIData): Datos del CFDI
        
    Returns:
        dict: Resumen con los datos principales
    """
    return {
        'folio_completo': f"{cfdi_data.serie}-{cfdi_data.folio}" if cfdi_data.serie else cfdi_data.folio,
        'fecha_emision': cfdi_data.fecha_emision.strftime('%d/%m/%Y') if cfdi_data.fecha_emision else None,
        'emisor': cfdi_data.emisor_nombre or cfdi_data.emisor_rfc,
        'receptor': cfdi_data.receptor_nombre or cfdi_data.receptor_rfc,
        'total': f"${cfdi_data.total:,.2f} {cfdi_data.moneda}" if cfdi_data.total else None,
        'uuid': cfdi_data.uuid,
        'archivo': cfdi_data.archivo_origen
    }


