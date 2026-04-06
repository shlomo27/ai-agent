"""
Interactive CLI questionnaire for setting up advertising campaigns.
Uses Rich library for beautiful terminal output.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.columns import Columns
from rich import box

from models.campaign import (
    Campaign, MarketingGoal, GOAL_LABELS_HE, TargetAudience, CampaignStatus
)
from config import SUPPORTED_PLATFORMS

console = Console()


def run_questionnaire() -> Campaign:
    """
    Run the interactive campaign setup questionnaire.
    Returns a Campaign object with all the user's preferences.
    """
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🚀 ברוך הבא לעוזר הפרסום AI שלך![/bold cyan]\n"
        "[dim]נגדיר יחד את מטרות הפרסום שלך כדי שנוכל לעבוד בצורה הכי חכמה[/dim]",
        border_style="cyan",
    ))
    console.print()

    # Step 1: Business description
    console.print("[bold yellow]שלב 1/7: תיאור העסק[/bold yellow]")
    console.print("[dim]ספר לנו על העסק שלך[/dim]")
    business_name = Prompt.ask("  📛 שם העסק", default="העסק שלי")
    business_description = Prompt.ask(
        "  📝 תיאור קצר של העסק (מה אתה עושה?)",
        default="",
    )
    website_url = Prompt.ask("  🌐 כתובת האתר (אופציונלי)", default="")
    business_type = Prompt.ask(
        "  🏢 סוג העסק",
        choices=["tech", "retail", "restaurant", "service", "education", "health", "other"],
        default="other",
    )
    console.print()

    # Step 2: Marketing goals
    console.print("[bold yellow]שלב 2/7: מטרות שיווקיות[/bold yellow]")
    console.print("[dim]בחר את המטרות השיווקיות שלך (ניתן לבחור מספר)[/dim]")
    console.print()

    goal_table = Table(box=box.ROUNDED, show_header=True)
    goal_table.add_column("מספר", style="cyan", width=6)
    goal_table.add_column("מטרה", style="white")
    goal_table.add_column("תיאור", style="dim")

    goal_descriptions = {
        MarketingGoal.NEW_USERS: "גיוס לקוחות/משתמשים חדשים לעסק",
        MarketingGoal.BRAND_AWARENESS: "הגדלת המודעות למותג שלך",
        MarketingGoal.LEAD_GENERATION: "יצירת לידים ופניות חדשות",
        MarketingGoal.SALES: "הגדלת מכירות ישירות",
        MarketingGoal.ENGAGEMENT: "הגדלת מעורבות הקהל",
        MarketingGoal.TRAFFIC: "הגברת תנועה לאתר",
        MarketingGoal.COMMUNITY: "בניית קהילה מסביב למותג",
        MarketingGoal.RETENTION: "שימור ונאמנות לקוחות קיימים",
    }

    for i, (goal, label) in enumerate(GOAL_LABELS_HE.items(), 1):
        goal_table.add_row(str(i), label, goal_descriptions.get(goal, ""))

    console.print(goal_table)
    console.print()

    goals_input = Prompt.ask(
        "  בחר מספרי מטרות (מופרדים בפסיק, לדוגמה: 1,3,4)",
        default="1",
    )

    selected_goals = []
    goal_list = list(GOAL_LABELS_HE.keys())
    for num_str in goals_input.split(","):
        try:
            idx = int(num_str.strip()) - 1
            if 0 <= idx < len(goal_list):
                selected_goals.append(goal_list[idx])
        except (ValueError, IndexError):
            pass

    if not selected_goals:
        selected_goals = [MarketingGoal.NEW_USERS]

    console.print(f"  ✅ מטרות נבחרו: {', '.join(GOAL_LABELS_HE[g] for g in selected_goals)}")
    console.print()

    # Step 3: Target audience
    console.print("[bold yellow]שלב 3/7: קהל יעד[/bold yellow]")
    age_min = IntPrompt.ask("  👤 גיל מינימום", default=18)
    age_max = IntPrompt.ask("  👤 גיל מקסימום", default=55)
    locations = Prompt.ask("  📍 מיקומים (מופרדים בפסיק)", default="ישראל")
    interests = Prompt.ask(
        "  ❤️ תחומי עניין של הקהל (מופרדים בפסיק)",
        default="טכנולוגיה, עסקים",
    )
    audience_description = Prompt.ask("  📋 תיאור הקהל (אופציונלי)", default="")
    console.print()

    target_audience = TargetAudience(
        age_min=age_min,
        age_max=age_max,
        locations=[loc.strip() for loc in locations.split(",")],
        interests=[interest.strip() for interest in interests.split(",")],
        custom_description=audience_description,
    )

    # Step 4: Connected platforms
    console.print("[bold yellow]שלב 4/7: רשתות חברתיות[/bold yellow]")
    console.print("[dim]לאילו רשתות חברתיות אתה רוצה להתחבר?[/dim]")
    console.print()

    platform_panels = []
    for platform_name, platform_info in SUPPORTED_PLATFORMS.items():
        platform_panels.append(
            Panel(
                f"{platform_info['icon']} {platform_info['name_he']}\n[dim]{', '.join(platform_info['features'][:3])}[/dim]",
                width=20,
            )
        )

    console.print(Columns(platform_panels))
    console.print()

    platforms_input = Prompt.ask(
        "  בחר פלטפורמות (מופרדות בפסיק)",
        default="facebook,instagram",
    )
    selected_platforms = [p.strip().lower() for p in platforms_input.split(",") if p.strip() in SUPPORTED_PLATFORMS]

    if not selected_platforms:
        selected_platforms = ["facebook"]

    console.print(f"  ✅ פלטפורמות: {', '.join(selected_platforms)}")
    console.print()

    # Step 5: Content
    console.print("[bold yellow]שלב 5/7: סוג תוכן[/bold yellow]")
    has_videos = Confirm.ask("  🎬 האם יש לך סרטונים לפרסם?", default=False)
    has_images = Confirm.ask("  📸 האם יש לך תמונות לפרסם?", default=True)
    content_themes_input = Prompt.ask(
        "  🎯 נושאי תוכן ראשיים (מופרדים בפסיק)",
        default="טיפים מקצועיים, עדכוני מוצר",
    )
    tone = Prompt.ask(
        "  🎭 טון הפרסום",
        choices=["professional", "casual", "funny", "inspirational"],
        default="professional",
    )
    console.print()

    # Step 6: Posting frequency
    console.print("[bold yellow]שלב 6/7: תדירות פרסום[/bold yellow]")
    posting_freq = Prompt.ask(
        "  📅 תדירות פרסום מועדפת",
        choices=["daily", "multiple_daily", "weekly", "few_times_weekly"],
        default="daily",
    )
    console.print()

    # Step 7: Budget and competitors
    console.print("[bold yellow]שלב 7/7: תקציב ומתחרים[/bold yellow]")
    has_budget = Confirm.ask("  💰 האם יש תקציב לפרסום ממומן?", default=False)
    budget = None
    if has_budget:
        budget = float(Prompt.ask("  💵 תקציב חודשי משוער (בשקלים)", default="500"))

    competitors_input = Prompt.ask(
        "  🔍 שמות מתחרים לניטור (מופרדים בפסיק, אופציונלי)",
        default="",
    )
    competitors = [c.strip() for c in competitors_input.split(",") if c.strip()]

    keywords_input = Prompt.ask(
        "  🔑 מילות מפתח לתחום שלך (מופרדים בפסיק)",
        default="עסקים, ישראל",
    )
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]

    console.print()

    # Create campaign
    campaign = Campaign(
        name=f"קמפיין {business_name}",
        description=business_description,
        goals=selected_goals,
        target_audience=target_audience,
        platforms=selected_platforms,
        content_themes=[t.strip() for t in content_themes_input.split(",")],
        keywords=keywords,
        competitors=competitors,
        budget_monthly=budget,
        has_videos=has_videos,
        has_images=has_images,
        posting_frequency=posting_freq,
        status=CampaignStatus.ACTIVE,
        business_description=f"{business_name}: {business_description}",
        website_url=website_url,
        tone=tone,
    )

    # Summary
    console.print(Panel(
        f"[bold green]✅ הגדרת הקמפיין הושלמה![/bold green]\n\n"
        f"📌 **שם:** {campaign.name}\n"
        f"🎯 **מטרות:** {', '.join(GOAL_LABELS_HE[g] for g in campaign.goals)}\n"
        f"📱 **פלטפורמות:** {', '.join(campaign.platforms)}\n"
        f"👥 **גיל קהל:** {campaign.target_audience.age_min}-{campaign.target_audience.age_max}\n"
        f"📅 **תדירות:** {campaign.posting_frequency}\n"
        f"{'💰 תקציב: ₪' + str(budget) + '/חודש' if budget else ''}",
        title="סיכום הקמפיין",
        border_style="green",
    ))

    return campaign


def display_campaign_summary(campaign: Campaign) -> None:
    """Display a formatted campaign summary."""
    console.print()
    table = Table(title=f"📊 קמפיין: {campaign.name}", box=box.ROUNDED)
    table.add_column("פרמטר", style="cyan")
    table.add_column("ערך", style="white")

    table.add_row("מטרות", ", ".join(GOAL_LABELS_HE.get(g, g.value) for g in campaign.goals))
    table.add_row("פלטפורמות", ", ".join(campaign.platforms))
    table.add_row("גיל קהל", f"{campaign.target_audience.age_min}-{campaign.target_audience.age_max}")
    table.add_row("מיקומים", ", ".join(campaign.target_audience.locations))
    table.add_row("תחומי עניין", ", ".join(campaign.target_audience.interests[:5]))
    table.add_row("תדירות פרסום", campaign.posting_frequency)
    if campaign.budget_monthly:
        table.add_row("תקציב חודשי", f"₪{campaign.budget_monthly:,.0f}")

    console.print(table)


def ask_for_campaign_update(campaign: Campaign) -> Campaign:
    """Allow user to update campaign settings."""
    console.print("\n[bold]עדכון הגדרות הקמפיין[/bold]")
    if Confirm.ask("האם ברצונך לעדכן משהו?", default=False):
        return run_questionnaire()
    return campaign
