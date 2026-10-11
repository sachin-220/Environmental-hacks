"""
AERIS — Atmospheric Emission-Response Intelligence System
Main Command Line Interface (CLI)
"""
import sys
import os
from pathlib import Path
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import settings
from config.logging_config import setup_logging, get_logger
from processing.spatial_grid import d03_grid_manager, d01_grid_manager, haversine_distance_km
from processing.inversion import AtmosphericInversionEngine
from processing.plume import FirePlumeTransportEngine
from processing.quality import QualityControlValidator
from processing.feature_fusion import FeatureFusionPipeline

from collectors.firms import FirmsCollector
from collectors.openaq import OpenAQCollector
from collectors.era5 import ERA5Collector
from collectors.cams import CAMSCollector
from collectors.gfas import GFASCollector
from collectors.emissions import EmissionsCollector
from scripts.setup_demo_data import setup_demo_cache

setup_logging(settings.SAMEER_LOG_LEVEL)
logger = get_logger("cli")
console = Console()


def print_banner():
    """Display AERIS Project Banner"""
    banner_text = (
        "[bold cyan]AERIS[/bold cyan] — [bold white]Atmospheric Emission-Response Intelligence System[/bold white]\n"
        "[dim]High-resolution 72-hour Air Pollution–Weather Coupled Forecasting System for Delhi NCR (Phase 1)[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan"))


def cmd_system_status():
    """Display system status, configuration, domains, and credential validation"""
    print_banner()
    
    # Configuration Table
    table = Table(title="System & Environment Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    
    creds = settings.get_masked_credentials()
    table.add_row("Operating Mode", f"[bold yellow]{settings.SAMEER_MODE.upper()}[/bold yellow]")
    table.add_row("Log Level", settings.SAMEER_LOG_LEVEL)
    table.add_row("NASA FIRMS Key", creds["FIRMS_MAP_KEY"])
    table.add_row("OpenAQ API Key", creds["OPENAQ_API_KEY"])
    table.add_row("Copernicus CDS Key", creds["CDS_API_KEY"])
    table.add_row("Project Root", str(settings.BASE_DIR))
    table.add_row("Data Directory", str(settings.DATA_DIR))
    console.print(table)

    # Domain Table
    dom_table = Table(title="Nested Modeling Domains", show_header=True, header_style="bold blue")
    dom_table.add_column("Domain ID", style="cyan")
    dom_table.add_column("Name", style="white")
    dom_table.add_column("Resolution (km)", justify="right")
    dom_table.add_column("Bounds (W, S, E, N)", style="dim")
    dom_table.add_column("Source Resolution / Purpose", style="italic")

    for dom in settings.NESTED_DOMAINS:
        b = dom.bounds
        bounds_str = f"[{b.west}, {b.south}, {b.east}, {b.north}]"
        dom_table.add_row(dom.domain_id, dom.name, f"{dom.resolution_km} km", bounds_str, dom.source_resolution_note)
    console.print(dom_table)

    # Live Mode Validation Check
    if settings.SAMEER_MODE == "live":
        missing = settings.validate_live_credentials()
        if missing:
            console.print(f"[bold red]WARNING: Running in LIVE mode with missing credentials: {', '.join(missing)}[/bold red]")
        else:
            console.print("[bold green]All live API credentials successfully validated.[/bold green]")
    else:
        console.print("[bold green]Running in OFFLINE/DEMO mode. Local cached datasets will be utilized.[/bold green]")


def cmd_data_status():
    """Inspect raw, processed, and final data directories"""
    print_banner()
    table = Table(title="Data Storage Repository Status", show_header=True, header_style="bold yellow")
    table.add_column("Data Layer", style="cyan")
    table.add_column("Subdirectory", style="white")
    table.add_column("File Count", justify="right")
    table.add_column("Sample Files", style="dim")

    for root_layer, root_path in [("Raw", settings.DATA_RAW_DIR), ("Processed", settings.DATA_PROCESSED_DIR), ("Final", settings.DATA_FINAL_DIR)]:
        if root_path.exists():
            for p in root_path.iterdir():
                if p.is_dir():
                    files = [f.name for f in p.iterdir() if not f.name.startswith(".")]
                    table.add_row(root_layer, p.name, str(len(files)), ", ".join(files[:3]) or "[empty]")
                elif p.is_file() and not p.name.startswith("."):
                    table.add_row(root_layer, p.name, "1", p.name)

    console.print(table)


def cmd_data_collect(source: str):
    """Run data collection for a specific source"""
    print_banner()
    console.print(f"[bold cyan]Running collector for source:[/bold cyan] [bold yellow]{source.upper()}[/bold yellow]")
    
    collectors_map = {
        "firms": FirmsCollector,
        "openaq": OpenAQCollector,
        "era5": ERA5Collector,
        "cams": CAMSCollector,
        "gfas": GFASCollector,
        "emissions": EmissionsCollector
    }
    
    if source not in collectors_map:
        console.print(f"[bold red]Unknown data source '{source}'. Available: {list(collectors_map.keys())}[/bold red]")
        return

    collector = collectors_map[source]()
    df = collector.collect()
    
    if df.empty:
        console.print(f"[bold red]Collector '{source}' returned 0 records.[/bold red]")
    else:
        console.print(f"[bold green]Successfully collected {len(df)} records from {source}.[/bold green]")
        console.print(f"[dim]Columns: {', '.join(df.columns[:10])}...[/dim]")
        # Show first 5 rows
        table = Table(title=f"Sample Data ({source.upper()})", show_header=True, header_style="bold cyan")
        for col in df.columns[:8]:
            table.add_column(str(col))
        for _, row in df.head(5).iterrows():
            table.add_row(*[str(row[col]) for col in df.columns[:8]])
        console.print(table)


def cmd_data_validate():
    """Run quality control and physical validation across raw/final datasets"""
    print_banner()
    console.print("[bold cyan]Running Quality Control & Physical Range Validation...[/bold cyan]")
    
    final_csv = settings.DATA_FINAL_DIR / "canonical_hourly.csv"
    if not final_csv.exists():
        console.print("[yellow]Canonical final dataset not found. Running fusion pipeline first to validate output...[/yellow]")
        pipeline = FeatureFusionPipeline()
        pipeline.run_fusion()

    df = pd.read_csv(final_csv)
    cleaned_df, report = QualityControlValidator.clean_dataframe(df)

    table = Table(title="Quality Control Audit Report", show_header=True, header_style="bold green")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Total Records Examined", str(report["total_rows"]))
    table.add_row("Valid Records (Passed QC)", f"[bold green]{report['valid_count']}[/bold green]")
    table.add_row("Suspect Records Flagged", f"[yellow]{report['suspect_count']}[/yellow]")
    table.add_row("Duplicates Filtered", str(report["duplicates_removed"]))
    console.print(table)


def cmd_processing_grid():
    """Display spatial grid details and sample cells"""
    print_banner()
    console.print("[bold cyan]Spatial Grid Architecture for Delhi NCR (Domain D03 @ 3 km):[/bold cyan]")
    grid_df = d03_grid_manager.grid_df
    
    table = Table(title="Delhi NCR Inner Core Grid Cells (Sample)", show_header=True, header_style="bold cyan")
    table.add_column("Grid ID", style="magenta")
    table.add_column("Row / Col", justify="center")
    table.add_column("Latitude", justify="right")
    table.add_column("Longitude", justify="right")
    table.add_column("Resolution", justify="right")

    for _, row in grid_df.head(10).iterrows():
        table.add_row(
            row["grid_id"],
            f"R{row['row_idx']} / C{row['col_idx']}",
            f"{row['latitude']:.4f}°N",
            f"{row['longitude']:.4f}°E",
            f"{row['resolution_km']} km"
        )
    console.print(table)
    console.print(f"[bold green]Total active grid cells in D03 domain: {len(grid_df)} cells[/bold green]")


def cmd_processing_inversion():
    """Execute atmospheric inversion calculation over vertical atmospheric soundings"""
    print_banner()
    console.print("[bold cyan]Running Atmospheric Inversion & Vertical Stability Diagnostics...[/bold cyan]")
    
    demo_path = settings.DATASETS_SAMPLE_DIR / "03_vertical_atmosphere.csv"
    if not demo_path.exists():
        console.print("[red]Vertical atmosphere dataset not found.[/red]")
        return

    df = pd.read_csv(demo_path)
    inv_df = AtmosphericInversionEngine.process_vertical_dataset(df)

    table = Table(title="Atmospheric Inversion & Stability Results (Sample)", show_header=True, header_style="bold magenta")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Inversion?", justify="center")
    table.add_column("Strength (K)", justify="right")
    table.add_column("Base Height (m)", justify="right")
    table.add_column("Top Height (m)", justify="right")
    table.add_column("Lapse Rate (K/km)", justify="right")
    table.add_column("Stability", style="bold yellow")
    table.add_column("Diagnostic Type", style="dim")

    for _, row in inv_df.head(10).iterrows():
        inv_str = "[bold green]YES[/bold green]" if row["inversion_presence"] == 1 else "[dim]NO[/dim]"
        table.add_row(
            str(row["timestamp"]),
            inv_str,
            f"{row['inversion_strength']:.2f}",
            f"{row['inversion_height']:.0f}",
            f"{row['inversion_top']:.0f}",
            f"{row['vertical_temperature_gradient']:.2f}",
            str(row["stability_index"]),
            str(row["diagnostic_type"])
        )
    console.print(table)


def cmd_processing_plume():
    """Execute fire-to-wind plume transport scoring"""
    print_banner()
    console.print("[bold cyan]Running Regional Fire-to-Wind Plume Transport Diagnostic...[/bold cyan]")
    
    firms_col = FirmsCollector()
    fires_df = firms_col.collect()
    
    # Evaluate with North-Westerly wind scenario (typical winter stubble burning transport: U=-2.5, V=-2.0)
    score_dict = FirePlumeTransportEngine.compute_regional_plume_score(
        fires_df=fires_df,
        u_wind=-2.5,
        v_wind=-2.0
    )

    table = Table(title="Regional Plume Inflow Assessment for Delhi NCR", show_header=True, header_style="bold yellow")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Active Fire Hotspots Detected", str(score_dict["fire_count"]))
    table.add_row("Total Fire Radiative Power (FRP)", f"{score_dict['fire_frp']:.1f} MW")
    table.add_row("Average Detection Confidence", f"{score_dict['fire_confidence']:.1f}%")
    table.add_row("Nearest Fire Distance to Delhi NCR", f"{score_dict['nearest_fire_distance']} km" if score_dict['nearest_fire_distance'] else "N/A")
    table.add_row("Active Upwind Fires (Direct Trajectory)", f"[bold red]{score_dict['upwind_fire_count']}[/bold red]")
    table.add_row("Upwind Fire Radiative Power", f"[bold red]{score_dict['upwind_fire_frp']:.1f} MW[/bold red]")
    table.add_row("Mean Upwind Distance", f"{score_dict['upwind_fire_distance']} km" if score_dict['upwind_fire_distance'] else "N/A")
    table.add_row("Wind-Fire Angle Offset", f"{score_dict['wind_fire_angle']}°" if score_dict['wind_fire_angle'] else "N/A")
    table.add_row("Integrated Plume Transport Score (0-100)", f"[bold yellow]{score_dict['plume_transport_score']:.2f} / 100.0[/bold yellow]")
    console.print(table)


def cmd_processing_fusion():
    """Execute end-to-end feature fusion pipeline"""
    print_banner()
    console.print("[bold cyan]Executing End-to-End Canonical Feature Fusion Pipeline...[/bold cyan]")
    pipeline = FeatureFusionPipeline()
    final_df = pipeline.run_fusion(save_output=True)
    
    table = Table(title="Canonical SAMEER Dataset (Preview)", show_header=True, header_style="bold cyan")
    preview_cols = ["timestamp", "grid_id", "temperature_2m", "pm25", "inversion_strength", "stability_index", "plume_transport_score", "provenance"]
    for col in preview_cols:
        table.add_column(col)
        
    for _, row in final_df.head(8).iterrows():
        table.add_row(
            str(row["timestamp"])[:19],
            str(row["grid_id"]),
            f"{row['temperature_2m']:.1f} K" if pd.notna(row['temperature_2m']) else "N/A",
            f"{row['pm25']:.1f}" if pd.notna(row['pm25']) else "N/A",
            f"{row['inversion_strength']:.2f} K" if pd.notna(row['inversion_strength']) else "N/A",
            str(row["stability_index"]),
            f"{row['plume_transport_score']:.1f}",
            str(row["provenance"])
        )
    console.print(table)
    console.print(f"[bold green]Successfully generated Canonical SAMEER Dataset with {len(final_df)} records.[/bold green]")
    console.print(f"[bold white]Saved to:[/bold white] [green]{settings.DATA_FINAL_DIR / 'canonical_hourly.parquet'}[/green] and [green]{settings.DATA_FINAL_DIR / 'canonical_hourly.csv'}[/green]")


def cmd_demo_setup():
    """Setup demo data environment from sample packs"""
    print_banner()
    console.print("[bold cyan]Setting up demonstration environment from sample datasets...[/bold cyan]")
    ok = setup_demo_cache()
    if ok:
        console.print("[bold green]Demo cache initialized successfully.[/bold green]")
    else:
        console.print("[bold red]Failed to initialize demo cache.[/bold red]")


def print_help():
    """Display available CLI commands"""
    print_banner()
    console.print("""[bold white]Available Commands:[/bold white]

  [bold cyan]System & Status:[/bold cyan]
    python main.py system status         Display system configuration, API keys, and domains
    python main.py data status           Display data repository storage status
    python main.py demo setup            Seed local data cache from demonstration dataset pack

  [bold cyan]Data Collectors:[/bold cyan]
    python main.py data firms            Collect active fire hotspots (NASA FIRMS)
    python main.py data openaq           Collect ground air quality measurements (OpenAQ)
    python main.py data era5             Collect surface & vertical meteorology (ERA5 CDS)
    python main.py data cams             Collect regional atmospheric composition (CAMS)
    python main.py data gfas             Collect biomass burning flux estimates (GFAS)
    python main.py data emissions        Collect anthropogenic emission inventories
    python main.py data validate         Run quality control & physical bounds audit

  [bold cyan]Processing & Diagnostics:[/bold cyan]
    python main.py processing grid       Generate and inspect nested modeling grid cells
    python main.py processing inversion  Compute vertical lapse rates and thermal inversion metrics
    python main.py processing plume      Compute upwind fire plume transport scoring
    python main.py processing fusion     Run end-to-end feature fusion into Canonical SAMEER dataset
""")


def main():
    args = sys.argv[1:]
    if not args:
        print_help()
        return

    category = args[0].lower()
    subcmd = args[1].lower() if len(args) > 1 else ""

    if category == "system" and subcmd == "status":
        cmd_system_status()
    elif category == "demo" and subcmd == "setup":
        cmd_demo_setup()
    elif category == "data":
        if subcmd == "status":
            cmd_data_status()
        elif subcmd == "validate":
            cmd_data_validate()
        elif subcmd in ["firms", "openaq", "era5", "cams", "gfas", "emissions"]:
            cmd_data_collect(subcmd)
        else:
            print_help()
    elif category == "processing":
        if subcmd == "grid":
            cmd_processing_grid()
        elif subcmd == "inversion":
            cmd_processing_inversion()
        elif subcmd == "plume":
            cmd_processing_plume()
        elif subcmd == "fusion":
            cmd_processing_fusion()
        else:
            print_help()
    else:
        print_help()


if __name__ == "__main__":
    main()
