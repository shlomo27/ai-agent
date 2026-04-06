#!/usr/bin/env python3
"""
AI Advertising Agent - Personal Marketing Assistant
Powered by Claude claude-opus-4-6 with adaptive thinking

Usage:
    python main.py start          - Start interactive chat mode
    python main.py campaign       - Create a new campaign with questionnaire
    python main.py connect        - Connect a social media platform
    python main.py serve          - Start the REST API server
    python main.py post           - Post content to platforms
    python main.py analytics      - View analytics dashboard
    python main.py recommend      - Get platform recommendations
"""
from __future__ import annotations
import asyncio
import logging
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box
from rich.live import Live
from rich.spinner import Spinner

from config import config, SUPPORTED_PLATFORMS

app = typer.Typer(
    name="advertising-agent",
    help="🚀 עוזר פרסום AI - Personal AI Advertising Assistant",
    no_args_is_help=True,
)
console = Console()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def _check_api_key():
    """Verify the Anthropic API key is configured."""
    if not config.ANTHROPIC_API_KEY or config.ANTHROPIC_API_KEY == "your_anthropic_api_key_here":
        console.print(Panel(
            "[red]❌ ANTHROPIC_API_KEY לא מוגדר![/red]\n\n"
            "1. העתק את הקובץ: [cyan]cp .env.example .env[/cyan]\n"
            "2. ערוך את הקובץ .env והוסף את המפתח שלך\n"
            "3. קבל מפתח API בכתובת: [link]https://console.anthropic.com[/link]",
            title="הגדרה נדרשת",
            border_style="red",
        ))
        raise typer.Exit(1)


@app.command()
def start():
    """
    🤖 הפעל את עוזר הפרסום AI במצב שיחה אינטראקטיבי.
    Start the AI advertising assistant in interactive chat mode.
    """
    _check_api_key()

    console.print()
    console.print(Panel.fit(
        "[bold cyan]🚀 עוזר הפרסום AI שלך מוכן![/bold cyan]\n\n"
        "[white]אני כאן לעזור לך עם:[/white]\n"
        "• 📱 פרסום ברשתות חברתיות\n"
        "• 🎯 מציאת קהל יעד\n"
        "• ✍️ יצירת תוכן\n"
        "• 📊 ניתוח ביצועים\n"
        "• 💰 פרסום ממומן\n\n"
        "[dim]הקלד 'עזרה' לרשימת פקודות | 'יציאה' לסיום[/dim]",
        border_style="cyan",
    ))
    console.print()

    demo_note = "[yellow]⚠️  מצב דמו פעיל - אין פעולות אמיתיות ברשתות החברתיות[/yellow]" if config.DEMO_MODE else "[green]✅ מצב חי - פעולות אמיתיות יתבצעו[/green]"
    console.print(demo_note)
    console.print()

    asyncio.run(_run_interactive_chat())


async def _run_interactive_chat():
    """Run the interactive chat loop."""
    from agent import AdvertisingAgent

    agent = AdvertisingAgent()

    # Auto-connect platforms in demo mode
    if config.DEMO_MODE:
        console.print("[dim]מתחבר לפלטפורמות (מצב דמו)...[/dim]")
        await agent.connect_all_platforms()
        console.print("[dim]✅ מחובר לכל הפלטפורמות[/dim]")
        console.print()

    try:
        while True:
            try:
                user_input = Prompt.ask("[bold cyan]אתה[/bold cyan]")
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]להתראות! 👋[/dim]")
                break

            if not user_input.strip():
                continue

            if user_input.lower() in ["יציאה", "exit", "quit", "q"]:
                console.print("[dim]להתראות! 👋[/dim]")
                break

            if user_input.lower() in ["עזרה", "help", "?"]:
                _show_help()
                continue

            if user_input.lower() in ["נקה", "clear", "cls"]:
                agent.clear_history()
                console.clear()
                console.print("[dim]היסטוריית השיחה נוקתה[/dim]")
                continue

            # Show thinking indicator
            console.print()
            with Live(Spinner("dots", text="[dim]מעבד...[/dim]"), refresh_per_second=10):
                response = await agent.chat(user_input)

            console.print()
            console.print(Panel(
                response,
                title="[bold green]🤖 מפרסם[/bold green]",
                border_style="green",
            ))
            console.print()

    finally:
        await agent.close()


def _show_help():
    """Display help information."""
    table = Table(title="📚 פקודות זמינות", box=box.ROUNDED)
    table.add_column("פקודה", style="cyan")
    table.add_column("תיאור", style="white")

    commands = [
        ("פרסם ב[פייסבוק] - [תוכן]", "פרסם פוסט לרשת חברתית"),
        ("מצא קהל יעד ב[פייסבוק] עבור [נושא]", "חפש משתמשים רלוונטיים"),
        ("צור לוח תוכן", "קבל תכנון תוכן לחודש הקרוב"),
        ("נתח ביצועים", "קבל דו\"ח ביצועים"),
        ("המלץ על פלטפורמות", "קבל המלצות לרשתות חדשות"),
        ("הקם קמפיין בפייסבוק אדס", "הנחיה להקמת פרסום ממומן"),
        ("מה הזמנים הטובים לפרסם", "קבל המלצת שעות פרסום"),
        ("צור האשטגים עבור [נושא]", "קבל האשטגים מומלצים"),
        ("עקוב אחרי [משתמש]", "עקוב אחרי משתמש ברשת"),
        ("הגב לפוסטים", "עיין בפיד והגב לפוסטים"),
        ("נקה", "נקה היסטוריית שיחה"),
        ("יציאה", "סיום התוכנית"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(table)
    console.print()


@app.command()
def campaign():
    """
    📋 צור קמפיין פרסום חדש באמצעות שאלון אינטראקטיבי.
    Create a new advertising campaign with interactive questionnaire.
    """
    _check_api_key()

    from questionnaire import run_questionnaire, display_campaign_summary

    try:
        campaign_obj = run_questionnaire()
        display_campaign_summary(campaign_obj)

        console.print()
        if Confirm.ask("האם להפעיל את הקמפיין עכשיו?", default=True):
            asyncio.run(_run_campaign(campaign_obj))
        else:
            console.print("[dim]הקמפיין נשמר. הפעל עם 'python main.py start' כשתהיה מוכן.[/dim]")

    except KeyboardInterrupt:
        console.print("\n[dim]השאלון בוטל.[/dim]")


async def _run_campaign(campaign_obj):
    """Run a campaign using the agent."""
    from agent import AdvertisingAgent
    agent = AdvertisingAgent()

    try:
        await agent.connect_all_platforms()

        campaign_brief = (
            f"התחל קמפיין פרסום עבור: {campaign_obj.business_description}\n"
            f"מטרות: {', '.join(g.value for g in campaign_obj.goals)}\n"
            f"פלטפורמות: {', '.join(campaign_obj.platforms)}\n"
            f"קהל יעד: {campaign_obj.target_audience.custom_description or 'כללי'}\n"
            f"נושאי תוכן: {', '.join(campaign_obj.content_themes)}\n\n"
            f"אנא: 1) מצא קהל יעד רלוונטי 2) הצע תוכן 3) צור לוח תוכן 4) המלץ על אסטרטגיה"
        )

        with Live(Spinner("dots", text="[dim]מעבד קמפיין...[/dim]"), refresh_per_second=10):
            response = await agent.chat(campaign_brief)

        console.print()
        console.print(Panel(response, title="[bold green]🚀 תכנית הקמפיין[/bold green]", border_style="green"))

    finally:
        await agent.close()


@app.command()
def connect(
    platform: str = typer.Argument(help="שם הפלטפורמה (facebook, instagram, twitter, linkedin, youtube, tiktok)"),
):
    """
    🔗 חבר רשת חברתית לעוזר הפרסום.
    Connect a social media platform to the agent.
    """
    if platform not in SUPPORTED_PLATFORMS:
        console.print(f"[red]❌ פלטפורמה לא מוכרת: {platform}[/red]")
        console.print(f"[dim]פלטפורמות זמינות: {', '.join(SUPPORTED_PLATFORMS.keys())}[/dim]")
        raise typer.Exit(1)

    asyncio.run(_connect_platform(platform))


async def _connect_platform(platform_name: str):
    """Connect to a specific platform."""
    from agent import AdvertisingAgent

    agent = AdvertisingAgent()
    try:
        console.print(f"[dim]מתחבר ל{SUPPORTED_PLATFORMS[platform_name]['name_he']}...[/dim]")
        account = await agent.connect_platform(platform_name)

        if account and account.is_connected:
            console.print(Panel(
                f"✅ מחובר בהצלחה!\n\n"
                f"👤 **שם משתמש:** {account.username}\n"
                f"👥 **עוקבים:** {account.followers_count:,}\n"
                f"📝 **פוסטים:** {account.posts_count:,}",
                title=f"{SUPPORTED_PLATFORMS[platform_name]['icon']} {SUPPORTED_PLATFORMS[platform_name]['name_he']}",
                border_style="green",
            ))
        else:
            console.print(f"[red]❌ חיבור נכשל. בדוק את הגדרות ה-API בקובץ .env[/red]")
    finally:
        await agent.close()


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="כתובת IP"),
    port: int = typer.Option(8000, help="פורט"),
    reload: bool = typer.Option(False, help="Hot reload"),
):
    """
    🌐 הפעל את ה-API server.
    Start the REST API server.
    """
    import uvicorn

    console.print(Panel(
        f"[bold cyan]🌐 מפעיל API Server[/bold cyan]\n\n"
        f"📡 כתובת: http://{host}:{port}\n"
        f"📚 תיעוד: http://{host}:{port}/docs\n"
        f"🔄 Hot Reload: {'כן' if reload else 'לא'}",
        border_style="cyan",
    ))

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=config.LOG_LEVEL.lower(),
    )


@app.command()
def analytics(
    platform: Optional[str] = typer.Option(None, help="פלטפורמה ספציפית"),
    days: int = typer.Option(30, help="מספר ימים"),
):
    """
    📊 הצג דשבורד ניתוח ביצועים.
    Display performance analytics dashboard.
    """
    _check_api_key()
    asyncio.run(_show_analytics(platform, days))


async def _show_analytics(platform: Optional[str], days: int):
    """Show analytics in the terminal."""
    from agent import AdvertisingAgent
    from tools.analytics_tools import get_campaign_performance, compare_platforms_performance

    agent = AdvertisingAgent()
    try:
        await agent.connect_all_platforms()

        console.print(f"[dim]מביא נתוני {days} ימים...[/dim]")

        if platform:
            from tools.analytics_tools import get_audience_insights
            data = await get_audience_insights(platform)
            console.print(Panel(
                str(data),
                title=f"📊 תובנות {platform}",
                border_style="blue",
            ))
        else:
            data = await compare_platforms_performance(days=days)

            table = Table(title=f"📊 השוואת ביצועים - {days} ימים אחרונים", box=box.ROUNDED)
            table.add_column("פלטפורמה", style="cyan")
            table.add_column("מעורבות %", style="yellow")
            table.add_column("חשיפה", style="green")
            table.add_column("עוקבים חדשים", style="blue")

            for platform_name, metrics in data.get("platforms", {}).items():
                if isinstance(metrics, dict) and "error" not in metrics:
                    table.add_row(
                        f"{SUPPORTED_PLATFORMS.get(platform_name, {}).get('icon', '📱')} {platform_name}",
                        f"{metrics.get('engagement_rate', 0):.1f}%",
                        f"{metrics.get('reach', 0):,}",
                        f"+{metrics.get('followers_gained', 0):,}",
                    )

            console.print(table)
            if data.get("insight"):
                console.print(f"\n💡 [bold]{data['insight']}[/bold]")

    finally:
        await agent.close()


@app.command()
def recommend(
    platforms: str = typer.Option("", help="פלטפורמות מחוברות (מופרדות בפסיק)"),
    goals: str = typer.Option("new_users,brand_awareness", help="מטרות שיווקיות"),
):
    """
    💡 קבל המלצות על פלטפורמות פרסום חדשות.
    Get recommendations for new advertising platforms.
    """
    from agent import AdvertisingAgent

    agent = AdvertisingAgent()
    connected = [p.strip() for p in platforms.split(",") if p.strip()]
    goals_list = [g.strip() for g in goals.split(",") if g.strip()]

    recs = agent._get_platform_recommendations(connected, goals_list)

    table = Table(title="💡 המלצות פלטפורמות", box=box.ROUNDED)
    table.add_column("פלטפורמה", style="cyan")
    table.add_column("סיבות", style="white")
    table.add_column("יתרונות", style="dim")

    for rec in recs.get("recommendations", []):
        platform_info = SUPPORTED_PLATFORMS.get(rec["platform"], {})
        table.add_row(
            f"{platform_info.get('icon', '📱')} {rec.get('platform_name_he', rec['platform'])}",
            "\n".join(rec.get("reasons", [])[:2]),
            ", ".join(rec.get("best_for", [])[:3]),
        )

    console.print(table)

    if recs.get("top_recommendation"):
        top = recs["top_recommendation"]
        console.print(f"\n🏆 [bold]המלצה עיקרית:[/bold] {top.get('platform_name_he', top.get('platform', ''))}")
        console.print(f"   {', '.join(top.get('reasons', []))}")


if __name__ == "__main__":
    app()
