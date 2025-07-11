#!/usr/bin/env python3
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from src.services.catalog import CatalogService
from src.services.google_auth import GoogleAuthService
from src.utils.logger import logger
from src.utils.config import GEMINI_API_KEY, INSTAGRAM_USERNAME

console = Console()


@click.group()
def cli():
    """
    🎵 Vinyl Instagram Bot - Automatização de vendas de discos de vinil
    
    Use os comandos abaixo para gerenciar seu catálogo e publicações.
    """
    pass


@cli.command()
def setup():
    """🔧 Configura autenticação com Google e testa conexões"""
    console.print("\n[bold blue]🔧 Configurando autenticação...[/bold blue]\n")
    
    try:
        # Testa Google APIs
        auth_service = GoogleAuthService()
        if auth_service.test_connection():
            console.print("[green]✅ Google APIs configuradas com sucesso![/green]")
        else:
            console.print("[red]❌ Erro na configuração do Google[/red]")
            return
        
        # Verifica configurações
        console.print("\n[bold]📋 Configurações atuais:[/bold]")
        console.print(f"  • Gemini API: {'✅ Configurada' if GEMINI_API_KEY else '❌ Não configurada'}")
        console.print(f"  • Instagram: {'✅ Configurado' if INSTAGRAM_USERNAME else '❌ Não configurado'}")
        
        if not GEMINI_API_KEY:
            console.print("\n[yellow]⚠️  Configure GEMINI_API_KEY no arquivo .env para análise de imagens[/yellow]")
        
        if not INSTAGRAM_USERNAME:
            console.print("[yellow]⚠️  Configure credenciais do Instagram no arquivo .env para publicação[/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


@cli.command()
@click.option('--limit', '-l', type=int, help='Número máximo de discos para processar')
def scan(limit):
    """📸 Escaneia imagens do Drive e cataloga discos"""
    console.print("\n[bold blue]📸 Iniciando escaneamento e catalogação...[/bold blue]\n")
    
    try:
        catalog = CatalogService()
        count = catalog.scan_and_catalog(limit)
        
        if count > 0:
            console.print(f"\n[green]✅ {count} discos catalogados com sucesso![/green]")
        else:
            console.print("\n[yellow]⚠️  Nenhum disco foi catalogado[/yellow]")
            
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


@cli.command()
@click.option('--limit', '-l', type=int, help='Número máximo de posts para publicar')
@click.option('--dry-run', is_flag=True, help='Simula publicação sem postar')
def publish(limit, dry_run):
    """📱 Publica discos pendentes no Instagram"""
    console.print("\n[bold blue]📱 Iniciando publicação no Instagram...[/bold blue]\n")
    
    if dry_run:
        console.print("[yellow]⚠️  Modo simulação ativado - nenhum post será publicado[/yellow]\n")
    
    try:
        catalog = CatalogService()
        
        # Lista pendentes primeiro
        pending = catalog.list_catalog('pendente')
        if not pending:
            console.print("[yellow]Nenhum disco pendente para publicação[/yellow]")
            return
        
        console.print(f"[cyan]📋 {len(pending)} discos pendentes[/cyan]\n")
        
        if dry_run:
            # Mostra o que seria publicado
            for i, vinyl in enumerate(pending[:limit] if limit else pending, 1):
                console.print(f"{i}. {vinyl['Nome']} - {vinyl['Artista']}")
        else:
            # Publica de verdade
            count = catalog.publish_pending(limit)
            
            if count > 0:
                console.print(f"\n[green]✅ {count} posts publicados com sucesso![/green]")
            else:
                console.print("\n[yellow]⚠️  Nenhum post foi publicado[/yellow]")
                
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


@cli.command()
@click.option('--status', '-s', type=click.Choice(['todos', 'pendente', 'publicado', 'vendido']), 
              default='todos', help='Filtrar por status')
@click.option('--limit', '-l', type=int, help='Número máximo de registros')
def list(status, limit):
    """📋 Lista discos catalogados"""
    console.print(f"\n[bold blue]📋 Listando discos ({status})...[/bold blue]\n")
    
    try:
        catalog = CatalogService()
        vinyls = catalog.list_catalog(None if status == 'todos' else status)
        
        if not vinyls:
            console.print("[yellow]Nenhum disco encontrado[/yellow]")
            return
        
        # Limita resultados se especificado
        if limit:
            vinyls = vinyls[:limit]
        
        # Cria tabela
        table = Table(title=f"Discos Catalogados ({len(vinyls)} registros)")
        
        table.add_column("#", style="cyan", width=4)
        table.add_column("Nome", style="magenta")
        table.add_column("Artista", style="green")
        table.add_column("Ano", width=6)
        table.add_column("Preço", width=10)
        table.add_column("Status", width=10)
        table.add_column("Publicado", width=16)
        
        for i, vinyl in enumerate(vinyls, 1):
            status_color = {
                'pendente': 'yellow',
                'publicado': 'green',
                'vendido': 'blue'
            }.get(vinyl.get('Status', '').lower(), 'white')
            
            table.add_row(
                str(i),
                vinyl.get('Nome', '-')[:30],
                vinyl.get('Artista', '-')[:20],
                vinyl.get('Ano', '-'),
                vinyl.get('Preço', '-'),
                f"[{status_color}]{vinyl.get('Status', '-')}[/{status_color}]",
                vinyl.get('Data Publicação', '-')
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


@cli.command()
@click.argument('row', type=int)
@click.argument('price', type=float)
def price(row, price):
    """💰 Atualiza preço de um disco (linha da planilha)"""
    console.print(f"\n[bold blue]💰 Atualizando preço...[/bold blue]\n")
    
    try:
        catalog = CatalogService()
        
        if catalog.update_price(row, price):
            console.print(f"[green]✅ Preço atualizado para R$ {price:.2f} na linha {row}[/green]")
        else:
            console.print("[red]❌ Erro ao atualizar preço[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


@cli.command()
def stats():
    """📊 Exibe estatísticas do catálogo"""
    console.print("\n[bold blue]📊 Estatísticas do Catálogo[/bold blue]\n")
    
    try:
        catalog = CatalogService()
        all_vinyls = catalog.list_catalog()
        
        if not all_vinyls:
            console.print("[yellow]Nenhum disco catalogado ainda[/yellow]")
            return
        
        # Calcula estatísticas
        total = len(all_vinyls)
        pendentes = sum(1 for v in all_vinyls if v.get('Status', '').lower() == 'pendente')
        publicados = sum(1 for v in all_vinyls if v.get('Status', '').lower() == 'publicado')
        vendidos = sum(1 for v in all_vinyls if v.get('Status', '').lower() == 'vendido')
        
        # Cria painel de estatísticas
        stats_text = f"""
[bold cyan]Total de Discos:[/bold cyan] {total}

[yellow]📋 Pendentes:[/yellow] {pendentes}
[green]✅ Publicados:[/green] {publicados}
[blue]💰 Vendidos:[/blue] {vendidos}

[dim]Taxa de publicação: {(publicados/total*100):.1f}%[/dim]
[dim]Taxa de conversão: {(vendidos/publicados*100 if publicados > 0 else 0):.1f}%[/dim]
        """
        
        panel = Panel(stats_text.strip(), title="📊 Resumo", border_style="blue")
        console.print(panel)
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


@cli.command()
def help():
    """❓ Exibe ajuda detalhada"""
    help_text = """
[bold cyan]🎵 Vinyl Instagram Bot - Guia de Uso[/bold cyan]

[bold]Comandos Disponíveis:[/bold]

  [green]setup[/green]    - Configura autenticação e testa conexões
  [green]scan[/green]     - Escaneia imagens do Drive e cataloga discos
  [green]publish[/green]  - Publica discos pendentes no Instagram
  [green]list[/green]     - Lista discos catalogados
  [green]price[/green]    - Atualiza preço de um disco
  [green]stats[/green]    - Exibe estatísticas do catálogo

[bold]Fluxo Recomendado:[/bold]

  1. Execute [cyan]setup[/cyan] para configurar autenticação
  2. Use [cyan]scan[/cyan] para catalogar novos discos
  3. Atualize preços com [cyan]price[/cyan]
  4. Publique com [cyan]publish[/cyan]

[bold]Exemplos:[/bold]

  vinyl-bot scan --limit 5          # Cataloga até 5 discos
  vinyl-bot list --status pendente  # Lista apenas pendentes
  vinyl-bot price 10 49.90          # Define preço R$ 49,90 na linha 10
  vinyl-bot publish --dry-run       # Simula publicação

[bold]Configuração:[/bold]

  Crie um arquivo [cyan].env[/cyan] baseado no [cyan].env.example[/cyan]
  Configure as credenciais necessárias
    """
    
    console.print(Panel(help_text.strip(), title="❓ Ajuda", border_style="green"))


if __name__ == '__main__':
    console.print("\n[bold cyan]🎵 Vinyl Instagram Bot[/bold cyan]\n")
    cli()