from enum import Enum

class ReportType(str, Enum):
    niche_analysis = "niche_analysis"
    diagnostics = "diagnostics"
    seo = "seo"
    seasonal = "seasonal"
    competitors = "competitors"