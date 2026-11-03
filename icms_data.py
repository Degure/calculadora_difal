# icms_data.py — Matriz ICMS 2025 e cálculo de DIFAL (standalone)
from typing import Dict, Optional

UFS_BRASIL = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RN', 'RS', 'RJ', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']

UF_ORIGEM_PADRAO = "SC"

NOMES_UF = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RJ": "Rio de Janeiro",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}

ICMS_INTERNA = {'AC': 19.0, 'AL': 19.0, 'AM': 20.0, 'AP': 18.0, 'BA': 20.5, 'CE': 20.0, 'DF': 20.0, 'ES': 17.0, 'GO': 19.0, 'MA': 22.0, 'MT': 17.0, 'MS': 17.0, 'MG': 18.0, 'PA': 19.0, 'PB': 20.0, 'PR': 19.5, 'PE': 20.5, 'PI': 21.0, 'RN': 18.0, 'RS': 17.0, 'RJ': 20.0, 'RO': 19.5, 'RR': 20.0, 'SC': 17.0, 'SP': 18.0, 'SE': 19.0, 'TO': 20.0}

ICMS_MATRIZ = {'AC': {'AC': 19.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'AL': {'AC': 12.0, 'AL': 19.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'AM': {'AC': 12.0, 'AL': 12.0, 'AM': 20.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'AP': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 18.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'BA': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 20.5, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'CE': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 20.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'DF': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 20.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'ES': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 17.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'GO': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 19.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'MA': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 22.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'MT': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 17.0, 'MS': 7.0, 'MG': 7.0, 'PA': 7.0, 'PB': 7.0, 'PR': 7.0, 'PE': 12.0, 'PI': 7.0, 'RN': 7.0, 'RS': 7.0, 'RJ': 12.0, 'RO': 7.0, 'RR': 7.0, 'SC': 12.0, 'SP': 7.0, 'SE': 12.0, 'TO': 7.0}, 'MS': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 17.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'MG': {'AC': 7.0, 'AL': 7.0, 'AM': 7.0, 'AP': 7.0, 'BA': 7.0, 'CE': 7.0, 'DF': 7.0, 'ES': 7.0, 'GO': 7.0, 'MA': 7.0, 'MT': 7.0, 'MS': 7.0, 'MG': 18.0, 'PA': 7.0, 'PB': 12.0, 'PR': 7.0, 'PE': 7.0, 'PI': 7.0, 'RN': 12.0, 'RS': 7.0, 'RJ': 7.0, 'RO': 7.0, 'RR': 12.0, 'SC': 7.0, 'SP': 12.0, 'SE': 7.0, 'TO': 7.0}, 'PA': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 19.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'PB': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 20.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'PR': {'AC': 7.0, 'AL': 7.0, 'AM': 7.0, 'AP': 7.0, 'BA': 7.0, 'CE': 7.0, 'DF': 7.0, 'ES': 7.0, 'GO': 7.0, 'MA': 7.0, 'MT': 7.0, 'MS': 7.0, 'MG': 12.0, 'PA': 7.0, 'PB': 7.0, 'PR': 19.5, 'PE': 7.0, 'PI': 7.0, 'RN': 7.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 7.0, 'RR': 7.0, 'SC': 12.0, 'SP': 7.0, 'SE': 12.0, 'TO': 7.0}, 'PE': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 20.5, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'PI': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 21.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'RN': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 18.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'RS': {'AC': 7.0, 'AL': 7.0, 'AM': 7.0, 'AP': 7.0, 'BA': 7.0, 'CE': 7.0, 'DF': 7.0, 'ES': 7.0, 'GO': 7.0, 'MA': 7.0, 'MT': 7.0, 'MS': 7.0, 'MG': 12.0, 'PA': 7.0, 'PB': 7.0, 'PR': 12.0, 'PE': 7.0, 'PI': 7.0, 'RN': 7.0, 'RS': 17.0, 'RJ': 7.0, 'RO': 7.0, 'RR': 12.0, 'SC': 7.0, 'SP': 12.0, 'SE': 7.0, 'TO': 7.0}, 'RJ': {'AC': 7.0, 'AL': 7.0, 'AM': 7.0, 'AP': 7.0, 'BA': 7.0, 'CE': 7.0, 'DF': 7.0, 'ES': 7.0, 'GO': 7.0, 'MA': 7.0, 'MT': 7.0, 'MS': 7.0, 'MG': 12.0, 'PA': 7.0, 'PB': 7.0, 'PR': 12.0, 'PE': 7.0, 'PI': 7.0, 'RN': 7.0, 'RS': 12.0, 'RJ': 20.0, 'RO': 7.0, 'RR': 7.0, 'SC': 12.0, 'SP': 7.0, 'SE': 12.0, 'TO': 7.0}, 'RO': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 19.5, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'RR': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 20.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 12.0}, 'SC': {'AC': 7.0, 'AL': 7.0, 'AM': 7.0, 'AP': 7.0, 'BA': 7.0, 'CE': 7.0, 'DF': 7.0, 'ES': 7.0, 'GO': 7.0, 'MA': 7.0, 'MT': 12.0, 'MS': 7.0, 'MG': 7.0, 'PA': 12.0, 'PB': 7.0, 'PR': 7.0, 'PE': 7.0, 'PI': 12.0, 'RN': 12.0, 'RS': 7.0, 'RJ': 7.0, 'RO': 12.0, 'RR': 7.0, 'SC': 17.0, 'SP': 7.0, 'SE': 7.0, 'TO': 7.0}, 'SP': {'AC': 7.0, 'AL': 7.0, 'AM': 7.0, 'AP': 7.0, 'BA': 7.0, 'CE': 7.0, 'DF': 7.0, 'ES': 7.0, 'GO': 7.0, 'MA': 7.0, 'MT': 7.0, 'MS': 7.0, 'MG': 12.0, 'PA': 7.0, 'PB': 7.0, 'PR': 12.0, 'PE': 7.0, 'PI': 7.0, 'RN': 7.0, 'RS': 12.0, 'RJ': 7.0, 'RO': 7.0, 'RR': 12.0, 'SC': 7.0, 'SP': 18.0, 'SE': 7.0, 'TO': 7.0}, 'SE': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 19.0, 'TO': 12.0}, 'TO': {'AC': 12.0, 'AL': 12.0, 'AM': 12.0, 'AP': 12.0, 'BA': 12.0, 'CE': 12.0, 'DF': 12.0, 'ES': 12.0, 'GO': 12.0, 'MA': 12.0, 'MT': 12.0, 'MS': 12.0, 'MG': 12.0, 'PA': 12.0, 'PB': 12.0, 'PR': 12.0, 'PE': 12.0, 'PI': 12.0, 'RN': 12.0, 'RS': 12.0, 'RJ': 12.0, 'RO': 12.0, 'RR': 12.0, 'SC': 12.0, 'SP': 12.0, 'SE': 12.0, 'TO': 20.0}}

# Produtos importados: alíquota interestadual fixa (Resolução Senado 13/2012)
ALIQUOTA_INTERESTADUAL_IMPORTADO = 4.0


def normalizar_uf(uf: Optional[str]) -> str:
    if not uf:
        return ""
    u = str(uf).strip().upper()
    if u in ICMS_INTERNA:
        return u
    # tenta pelo nome
    for sigla, nome in NOMES_UF.items():
        if nome.upper() == u or nome.upper().startswith(u):
            return sigla
    return u[:2] if len(u) >= 2 else u


def aliquota_interna(uf: str) -> float:
    return float(ICMS_INTERNA.get(normalizar_uf(uf), 18.0))


def aliquota_interestadual(origem: str, destino: str, origem_produto: str = "nacional") -> float:
    """
    Nacional: matriz ICMS 2025 origem→destino.
    Importado: 4% (mercadoria importada).
    """
    o = normalizar_uf(origem)
    d = normalizar_uf(destino)
    if (origem_produto or "nacional").lower().startswith("import"):
        return ALIQUOTA_INTERESTADUAL_IMPORTADO
    if o in ICMS_MATRIZ and d in ICMS_MATRIZ[o]:
        return float(ICMS_MATRIZ[o][d])
    if o == d:
        return aliquota_interna(d)
    return 12.0


def calcular_difal(
    valor_base: float,
    uf_destino: str,
    uf_origem: str = UF_ORIGEM_PADRAO,
    origem_produto: str = "nacional",
) -> dict:
    """
    Estimativa comercial de DIFAL:

        DIFAL = base × (alíquota interna DESTINO − alíquota interestadual) / 100

    - Nacional: interestadual pela matriz ICMS 2025
    - Importado: interestadual 4%
    Mesmo estado: DIFAL = 0
    Orientativo — validar com o fiscal na NF.
    """
    o = normalizar_uf(uf_origem) or UF_ORIGEM_PADRAO
    d = normalizar_uf(uf_destino)
    tipo = (origem_produto or "nacional").lower()
    if tipo.startswith("import"):
        tipo_label = "Importado"
    else:
        tipo_label = "Nacional"
        tipo = "nacional"

    base = float(valor_base or 0)
    resultado = {
        "uf_origem": o,
        "uf_destino": d,
        "nome_origem": NOMES_UF.get(o, o),
        "nome_destino": NOMES_UF.get(d, d),
        "origem_produto": tipo,
        "origem_produto_label": tipo_label,
        "valor_base": base,
        "aliquota_interna_destino": 0.0,
        "aliquota_interestadual": 0.0,
        "diferenca_pp": 0.0,
        "valor_icms_interestadual": 0.0,
        "valor_icms_interno_teorico": 0.0,
        "valor_difal": 0.0,
        "aplica": False,
        "observacao": "",
        "passos": [],
    }

    if not d or d not in ICMS_INTERNA:
        resultado["observacao"] = "Informe uma UF de destino válida."
        resultado["passos"].append("UF de destino inválida ou vazia.")
        return resultado

    interna = aliquota_interna(d)
    inter = aliquota_interestadual(o, d, tipo)
    resultado["aliquota_interna_destino"] = interna
    resultado["aliquota_interestadual"] = inter
    resultado["valor_icms_interestadual"] = round(base * inter / 100.0, 2)
    resultado["valor_icms_interno_teorico"] = round(base * interna / 100.0, 2)

    resultado["passos"].append(
        f"1) Base de cálculo (valor da operação / NF): R$ {base:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    resultado["passos"].append(
        f"2) Origem: {o} ({NOMES_UF.get(o, o)}) → Destino: {d} ({NOMES_UF.get(d, d)})"
    )
    resultado["passos"].append(
        f"3) Produto: {tipo_label}"
    )
    resultado["passos"].append(
        f"4) Alíquota interna do destino ({d}): {interna:.2f}%"
    )
    if tipo == "nacional":
        resultado["passos"].append(
            f"5) Alíquota interestadual ({o}→{d}) pela matriz ICMS 2025: {inter:.2f}%"
        )
    else:
        resultado["passos"].append(
            f"5) Alíquota interestadual para mercadoria importada: {inter:.2f}% (Res. Senado 13/2012)"
        )

    if o == d:
        resultado["observacao"] = (
            f"Operação interna ({o}). Não há DIFAL interestadual. "
            f"Alíquota interna: {interna:.1f}%."
        )
        resultado["passos"].append("6) Mesma UF de origem e destino → DIFAL = R$ 0,00")
        return resultado

    diff = interna - inter
    resultado["diferenca_pp"] = diff
    resultado["aplica"] = True
    resultado["passos"].append(
        f"6) Diferença de alíquotas: {interna:.2f}% − {inter:.2f}% = {diff:.2f} pontos percentuais"
    )

    if diff <= 0:
        resultado["valor_difal"] = 0.0
        resultado["observacao"] = (
            f"Diferença de alíquota ≤ 0 ({interna:.1f}% − {inter:.1f}%). DIFAL estimado zerado."
        )
        resultado["passos"].append("7) Diferença ≤ 0 → DIFAL = R$ 0,00")
        return resultado

    valor_difal = round(base * (diff / 100.0), 2)
    resultado["valor_difal"] = valor_difal
    base_fmt = f"{base:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    dif_fmt = f"{valor_difal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    resultado["passos"].append(
        f"7) DIFAL = base × diferença / 100 = {base_fmt} × {diff:.2f}% = R$ {dif_fmt}"
    )
    resultado["passos"].append(
        f"8) ICMS interestadual (destaque na NF): R$ {resultado['valor_icms_interestadual']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    resultado["observacao"] = (
        f"DIFAL estimado ({tipo_label}) = base × ({interna:.1f}% − {inter:.1f}%) = R$ {dif_fmt}. "
        f"{o} → {d}. Orientativo — validar com o fiscal na NF."
    )
    return resultado
