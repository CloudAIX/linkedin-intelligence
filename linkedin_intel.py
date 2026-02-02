#!/usr/bin/env python3
"""
LinkedIn Network Intelligence
Analyze your LinkedIn export to discover relationship insights.

Usage:
    python linkedin_intel.py --data ./linkedin_export/
    python linkedin_intel.py --example
    python linkedin_intel.py --warm-path "Stripe"
"""

import argparse
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import defaultdict
import math

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Connection:
    first_name: str
    last_name: str
    email: str
    company: str
    position: str
    connected_on: datetime

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

@dataclass
class Message:
    conversation_id: str
    sender: str
    recipient: str
    date: datetime
    content: str

    @property
    def is_deep(self) -> bool:
        """Check if message is substantive (100+ chars, questions, etc.)"""
        if len(self.content) < 100:
            return False
        shallow_phrases = ["congrats", "congratulations", "thanks", "thank you",
                         "happy birthday", "great post", "interesting"]
        content_lower = self.content.lower()
        if any(phrase in content_lower for phrase in shallow_phrases) and len(self.content) < 150:
            return False
        return True

@dataclass
class Endorsement:
    name: str
    skill: str
    date: datetime

@dataclass
class Recommendation:
    name: str
    date: datetime
    text: str

@dataclass
class RelationshipScore:
    name: str
    company: str
    half_life_strength: float  # 0-100
    vouch_score: float  # 0-100
    reciprocity_balance: int  # positive = they owe you
    last_meaningful_contact: Optional[datetime]
    days_since_contact: int
    shared_history: bool
    messages_exchanged: int
    recommendations_given: int
    recommendations_received: int
    endorsements_given: int
    endorsements_received: int

# ============================================================================
# LINKEDIN DATA PARSER
# ============================================================================

class LinkedInDataParser:
    """Parse LinkedIn export CSV files."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.connections: List[Connection] = []
        self.messages: List[Message] = []
        self.endorsements_given: List[Endorsement] = []
        self.endorsements_received: List[Endorsement] = []
        self.recommendations_given: List[Recommendation] = []
        self.recommendations_received: List[Recommendation] = []

    def parse_all(self):
        """Parse all available LinkedIn export files."""
        self._parse_connections()
        self._parse_messages()
        self._parse_endorsements()
        self._parse_recommendations()
        return self

    def _parse_connections(self):
        """Parse Connections.csv"""
        filepath = self.data_dir / "Connections.csv"
        if not filepath.exists():
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    connected_on = datetime.strptime(row.get('Connected On', ''), '%d %b %Y')
                except:
                    connected_on = datetime.now() - timedelta(days=365)

                self.connections.append(Connection(
                    first_name=row.get('First Name', ''),
                    last_name=row.get('Last Name', ''),
                    email=row.get('Email Address', ''),
                    company=row.get('Company', ''),
                    position=row.get('Position', ''),
                    connected_on=connected_on
                ))

    def _parse_messages(self):
        """Parse messages.csv"""
        filepath = self.data_dir / "messages.csv"
        if not filepath.exists():
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date = datetime.strptime(row.get('DATE', ''), '%Y-%m-%d %H:%M:%S UTC')
                except:
                    try:
                        date = datetime.strptime(row.get('DATE', '')[:10], '%Y-%m-%d')
                    except:
                        date = datetime.now()

                self.messages.append(Message(
                    conversation_id=row.get('CONVERSATION ID', ''),
                    sender=row.get('FROM', ''),
                    recipient=row.get('TO', ''),
                    date=date,
                    content=row.get('CONTENT', '')
                ))

    def _parse_endorsements(self):
        """Parse endorsement files."""
        # Endorsements Received
        filepath = self.data_dir / "Endorsement_Received_Info.csv"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.endorsements_received.append(Endorsement(
                        name=row.get('Endorser First Name', '') + ' ' + row.get('Endorser Last Name', ''),
                        skill=row.get('Skill Name', ''),
                        date=datetime.now()  # LinkedIn doesn't export dates
                    ))

        # Endorsements Given - similar pattern
        filepath = self.data_dir / "Endorsement_Given_Info.csv"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.endorsements_given.append(Endorsement(
                        name=row.get('First Name', '') + ' ' + row.get('Last Name', ''),
                        skill=row.get('Skill Name', ''),
                        date=datetime.now()
                    ))

    def _parse_recommendations(self):
        """Parse recommendation files."""
        # Recommendations Received
        filepath = self.data_dir / "Recommendations_Received.csv"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.recommendations_received.append(Recommendation(
                        name=row.get('First Name', '') + ' ' + row.get('Last Name', ''),
                        date=datetime.now(),
                        text=row.get('Recommendation', '')
                    ))

        # Recommendations Given
        filepath = self.data_dir / "Recommendations_Given.csv"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.recommendations_given.append(Recommendation(
                        name=row.get('First Name', '') + ' ' + row.get('Last Name', ''),
                        date=datetime.now(),
                        text=row.get('Recommendation', '')
                    ))

# ============================================================================
# ANALYSIS MODULES
# ============================================================================

class NetworkAnalyzer:
    """Analyze LinkedIn network data."""

    HALF_LIFE_DAYS = 180
    RECOMMENDATION_POINTS = 10
    ENDORSEMENT_POINTS = 2

    def __init__(self, parser: LinkedInDataParser, my_name: str = ""):
        self.parser = parser
        self.my_name = my_name
        self._build_indexes()

    def _build_indexes(self):
        """Build lookup indexes for fast analysis."""
        # Connection by name
        self.connections_by_name: Dict[str, Connection] = {}
        for conn in self.parser.connections:
            self.connections_by_name[conn.full_name.lower()] = conn

        # Messages by person
        self.messages_by_person: Dict[str, List[Message]] = defaultdict(list)
        for msg in self.parser.messages:
            # Index by sender and recipient
            self.messages_by_person[msg.sender.lower()].append(msg)
            self.messages_by_person[msg.recipient.lower()].append(msg)

        # Endorsements by person
        self.endorsements_received_by: Dict[str, int] = defaultdict(int)
        for e in self.parser.endorsements_received:
            self.endorsements_received_by[e.name.lower()] += 1

        self.endorsements_given_to: Dict[str, int] = defaultdict(int)
        for e in self.parser.endorsements_given:
            self.endorsements_given_to[e.name.lower()] += 1

        # Recommendations by person
        self.recommendations_received_from: Dict[str, int] = defaultdict(int)
        for r in self.parser.recommendations_received:
            self.recommendations_received_from[r.name.lower()] += 1

        self.recommendations_given_to: Dict[str, int] = defaultdict(int)
        for r in self.parser.recommendations_given:
            self.recommendations_given_to[r.name.lower()] += 1

    def calculate_relationship_scores(self) -> List[RelationshipScore]:
        """Calculate comprehensive relationship scores for all connections."""
        scores = []

        for conn in self.parser.connections:
            name_lower = conn.full_name.lower()

            # Get messages with this person
            messages = self.messages_by_person.get(name_lower, [])
            deep_messages = [m for m in messages if m.is_deep]

            # Last meaningful contact
            if deep_messages:
                last_contact = max(m.date for m in deep_messages)
            elif messages:
                last_contact = max(m.date for m in messages)
            else:
                last_contact = conn.connected_on

            days_since = (datetime.now() - last_contact).days

            # Half-life strength calculation
            half_lives_passed = days_since / self.HALF_LIFE_DAYS
            strength = 100 * math.pow(0.5, half_lives_passed)

            # Endorsements and recommendations
            endorsements_received = self.endorsements_received_by.get(name_lower, 0)
            endorsements_given = self.endorsements_given_to.get(name_lower, 0)
            recommendations_received = self.recommendations_received_from.get(name_lower, 0)
            recommendations_given = self.recommendations_given_to.get(name_lower, 0)

            # Reciprocity balance
            points_given = (recommendations_given * self.RECOMMENDATION_POINTS +
                          endorsements_given * self.ENDORSEMENT_POINTS)
            points_received = (recommendations_received * self.RECOMMENDATION_POINTS +
                             endorsements_received * self.ENDORSEMENT_POINTS)
            reciprocity = points_given - points_received  # Positive = they owe you

            # Vouch score calculation
            vouch = self._calculate_vouch_score(
                messages=messages,
                deep_messages=deep_messages,
                days_since=days_since,
                recommendations_received=recommendations_received,
                recommendations_given=recommendations_given,
                endorsements_received=endorsements_received
            )

            scores.append(RelationshipScore(
                name=conn.full_name,
                company=conn.company,
                half_life_strength=round(strength, 1),
                vouch_score=round(vouch, 1),
                reciprocity_balance=reciprocity,
                last_meaningful_contact=last_contact if messages else None,
                days_since_contact=days_since,
                shared_history=False,  # Would need job history to determine
                messages_exchanged=len(messages),
                recommendations_given=recommendations_given,
                recommendations_received=recommendations_received,
                endorsements_given=endorsements_given,
                endorsements_received=endorsements_received
            ))

        return scores

    def _calculate_vouch_score(self, messages, deep_messages, days_since,
                               recommendations_received, recommendations_given,
                               endorsements_received) -> float:
        """Calculate vouch score (0-100) predicting advocacy likelihood."""
        score = 0

        # Message depth (0-30)
        if not messages:
            score += 0
        elif not deep_messages:
            score += 5
        elif len(deep_messages) < 5:
            score += 15
        else:
            score += 30

        # Recency (0-20)
        if days_since > 730:  # 2 years
            score += 0
        elif days_since > 365:
            score += 5
        elif days_since > 180:
            score += 10
        else:
            score += 20

        # Recommendations (0-30)
        if recommendations_received > 0:
            score += 30
        elif recommendations_given > 0:
            score += 10

        # Endorsements (0-10)
        score += min(endorsements_received * 2, 10)

        # Shared history bonus (0-10) - simplified
        if len(messages) > 20:
            score += 10
        elif len(messages) > 10:
            score += 5

        return min(score, 100)

    def get_warmest_relationships(self, top_n: int = 20) -> List[RelationshipScore]:
        """Get warmest relationships by half-life strength."""
        scores = self.calculate_relationship_scores()
        return sorted(scores, key=lambda x: x.half_life_strength, reverse=True)[:top_n]

    def get_going_cold(self, top_n: int = 20) -> List[RelationshipScore]:
        """Get relationships that are going cold but worth saving."""
        scores = self.calculate_relationship_scores()
        # Filter to 30-70% strength (going cold but not dead)
        going_cold = [s for s in scores if 30 <= s.half_life_strength <= 70]
        # Sort by vouch score (prioritize valuable relationships)
        return sorted(going_cold, key=lambda x: x.vouch_score, reverse=True)[:top_n]

    def get_top_advocates(self, top_n: int = 20) -> List[RelationshipScore]:
        """Get people most likely to advocate for you."""
        scores = self.calculate_relationship_scores()
        return sorted(scores, key=lambda x: x.vouch_score, reverse=True)[:top_n]

    def get_reciprocity_balance(self) -> tuple:
        """Get people who owe you vs people you owe."""
        scores = self.calculate_relationship_scores()

        they_owe = sorted([s for s in scores if s.reciprocity_balance > 0],
                         key=lambda x: x.reciprocity_balance, reverse=True)
        you_owe = sorted([s for s in scores if s.reciprocity_balance < 0],
                        key=lambda x: x.reciprocity_balance)

        return they_owe[:15], you_owe[:15]

    def find_warm_paths(self, target_company: str) -> List[RelationshipScore]:
        """Find connections who might provide a path to target company."""
        scores = self.calculate_relationship_scores()

        # Direct connections at target
        direct = [s for s in scores
                  if target_company.lower() in s.company.lower()]

        # Sort by combined warmth and vouch score
        return sorted(direct, key=lambda x: x.half_life_strength + x.vouch_score,
                     reverse=True)[:10]

    def find_resurrection_opportunities(self) -> List[dict]:
        """Find dormant conversations worth reviving."""
        opportunities = []

        for conn in self.parser.connections:
            name_lower = conn.full_name.lower()
            messages = self.messages_by_person.get(name_lower, [])

            if not messages:
                continue

            # Look for "let's catch up" type patterns
            catch_up_phrases = ["catch up", "grab coffee", "get together",
                               "happy to help", "let me know", "would love to"]

            for msg in messages:
                content_lower = msg.content.lower()
                days_ago = (datetime.now() - msg.date).days

                # Find old messages with catch-up language
                if days_ago > 90 and any(phrase in content_lower for phrase in catch_up_phrases):
                    opportunities.append({
                        "name": conn.full_name,
                        "company": conn.company,
                        "last_message_date": msg.date,
                        "days_ago": days_ago,
                        "hook": msg.content[:100] + "...",
                        "type": "catch_up_promised"
                    })
                    break

        return sorted(opportunities, key=lambda x: x["days_ago"])[:20]

# ============================================================================
# REPORT GENERATOR
# ============================================================================

def generate_report(analyzer: NetworkAnalyzer) -> str:
    """Generate full network intelligence report."""

    warmest = analyzer.get_warmest_relationships(15)
    going_cold = analyzer.get_going_cold(15)
    advocates = analyzer.get_top_advocates(15)
    they_owe, you_owe = analyzer.get_reciprocity_balance()
    resurrections = analyzer.find_resurrection_opportunities()

    report = f"""# LinkedIn Network Intelligence Report
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Connections Analyzed**: {len(analyzer.parser.connections)}
**Messages Analyzed**: {len(analyzer.parser.messages)}

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total Connections | {len(analyzer.parser.connections)} |
| Strong Advocates (80+ vouch) | {len([a for a in advocates if a.vouch_score >= 80])} |
| Going Cold (need attention) | {len(going_cold)} |
| People Who Owe You Favors | {len(they_owe)} |
| Conversations to Resurrect | {len(resurrections)} |

---

## 🔥 Warmest Relationships

These connections have the strongest current relationship strength.

| Name | Company | Strength | Last Contact | Messages |
|------|---------|----------|--------------|----------|
"""

    for r in warmest[:10]:
        last = r.last_meaningful_contact.strftime("%Y-%m-%d") if r.last_meaningful_contact else "N/A"
        report += f"| {r.name} | {r.company} | {r.half_life_strength}% | {last} | {r.messages_exchanged} |\n"

    report += f"""
---

## ⚠️ Going Cold (Action Needed)

These valuable relationships are fading. Re-engage now.

| Name | Company | Strength | Days Since | Vouch Score |
|------|---------|----------|------------|-------------|
"""

    for r in going_cold[:10]:
        report += f"| {r.name} | {r.company} | {r.half_life_strength}% | {r.days_since_contact} | {r.vouch_score} |\n"

    report += f"""
---

## ⭐ Top Advocates (High Vouch Score)

These people would most likely advocate for you if asked.

| Name | Company | Vouch Score | Recommendations | Messages |
|------|---------|-------------|-----------------|----------|
"""

    for r in advocates[:10]:
        report += f"| {r.name} | {r.company} | {r.vouch_score} | {r.recommendations_received} received | {r.messages_exchanged} |\n"

    report += f"""
---

## 💰 Reciprocity Ledger

### They Owe You (Safe to Ask for Help)

| Name | Company | Points Given | Points Received | Balance |
|------|---------|--------------|-----------------|---------|
"""

    for r in they_owe[:8]:
        given = r.recommendations_given * 10 + r.endorsements_given * 2
        received = r.recommendations_received * 10 + r.endorsements_received * 2
        report += f"| {r.name} | {r.company} | {given} | {received} | +{r.reciprocity_balance} |\n"

    report += f"""
### You Owe Them (Consider Helping)

| Name | Company | Points Given | Points Received | Balance |
|------|---------|--------------|-----------------|---------|
"""

    for r in you_owe[:8]:
        given = r.recommendations_given * 10 + r.endorsements_given * 2
        received = r.recommendations_received * 10 + r.endorsements_received * 2
        report += f"| {r.name} | {r.company} | {given} | {received} | {r.reciprocity_balance} |\n"

    if resurrections:
        report += f"""
---

## 🔄 Conversation Resurrection Opportunities

Dormant threads with natural re-engagement hooks.

| Name | Company | Days Ago | Hook |
|------|---------|----------|------|
"""
        for opp in resurrections[:10]:
            report += f"| {opp['name']} | {opp['company']} | {opp['days_ago']} | {opp['hook'][:50]}... |\n"

    report += f"""
---

## Action Items

### This Week
1. Re-engage top 3 "Going Cold" relationships
2. Ask 1 person from "They Owe You" for a favor/intro
3. Help 1 person from "You Owe Them" proactively

### This Month
- Resurrect 5 dormant conversations
- Schedule catch-ups with top advocates
- Audit and update reciprocity balance

---

*Generated by LinkedIn Network Intelligence | GVRN-AI*
"""

    return report


def generate_warm_path_report(analyzer: NetworkAnalyzer, target: str) -> str:
    """Generate warm path report for a target company."""

    paths = analyzer.find_warm_paths(target)

    report = f"""# Warm Path Discovery: {target}
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## Direct Connections at {target}

"""

    if not paths:
        report += f"No direct connections found at {target}.\n\n"
        report += "### Suggestions:\n"
        report += "- Search for connections at competitor/partner companies\n"
        report += "- Look for 2nd-degree connections via your strongest advocates\n"
        report += "- Check for alumni connections from same schools\n"
    else:
        report += "| Name | Position | Warmth | Vouch | Approach |\n"
        report += "|------|----------|--------|-------|----------|\n"

        for r in paths:
            warmth = r.half_life_strength + r.vouch_score
            if warmth > 150:
                approach = "Direct ask - strong relationship"
            elif warmth > 100:
                approach = "Warm request after catch-up"
            else:
                approach = "Re-engage first, then ask"

            report += f"| {r.name} | {r.company} | {r.half_life_strength}% | {r.vouch_score} | {approach} |\n"

    return report

# ============================================================================
# SAMPLE DATA GENERATOR
# ============================================================================

def generate_sample_data(output_dir: Path):
    """Generate sample LinkedIn export data for testing."""

    output_dir.mkdir(parents=True, exist_ok=True)

    # Sample connections
    connections = [
        ["First Name", "Last Name", "Email Address", "Company", "Position", "Connected On"],
        ["Sarah", "Chen", "sarah@stripe.com", "Stripe", "Staff Engineer", "15 Jan 2024"],
        ["Mike", "Torres", "mike@acme.com", "Acme Corp", "VP Engineering", "20 Mar 2023"],
        ["Jennifer", "Liu", "jennifer@google.com", "Google", "Product Manager", "10 Jun 2022"],
        ["David", "Kim", "david@meta.com", "Meta", "AI Researcher", "05 Sep 2023"],
        ["Lisa", "Park", "lisa@startup.io", "TechStartup", "Founder", "12 Nov 2023"],
        ["James", "Wong", "james@amazon.com", "Amazon", "Solutions Architect", "18 Feb 2022"],
        ["Anna", "Lee", "anna@microsoft.com", "Microsoft", "Senior PM", "22 Jul 2024"],
        ["Chris", "Brown", "chris@openai.com", "OpenAI", "Research Engineer", "30 Aug 2023"],
        ["Rachel", "Green", "rachel@anthropic.com", "Anthropic", "ML Engineer", "14 Dec 2023"],
        ["Tom", "Wilson", "tom@netflix.com", "Netflix", "Engineering Manager", "08 Apr 2023"],
    ]

    with open(output_dir / "Connections.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(connections)

    # Sample messages
    messages = [
        ["CONVERSATION ID", "FROM", "TO", "DATE", "CONTENT"],
        ["conv1", "Sarah Chen", "Me", "2024-12-15 10:30:00 UTC", "Hey! Great to connect. Would love to catch up about AI infrastructure sometime."],
        ["conv1", "Me", "Sarah Chen", "2024-12-16 14:20:00 UTC", "Absolutely! I've been working on some interesting agent architectures. Let's grab coffee next week?"],
        ["conv1", "Sarah Chen", "Me", "2024-12-17 09:15:00 UTC", "Sounds great! Tuesday works for me. There's a cool AI meetup happening too if you're interested."],
        ["conv2", "Mike Torres", "Me", "2024-11-20 11:00:00 UTC", "Thanks for the intro to that candidate - they were excellent!"],
        ["conv2", "Me", "Mike Torres", "2024-11-21 16:45:00 UTC", "Glad it worked out! Let me know if you need any other referrals."],
        ["conv3", "Jennifer Liu", "Me", "2024-05-10 08:30:00 UTC", "Let's catch up soon! I'd love to hear about your new venture."],
        ["conv4", "David Kim", "Me", "2024-10-05 13:20:00 UTC", "Your post on AI governance was really insightful. Would love to discuss further."],
        ["conv4", "Me", "David Kim", "2024-10-06 10:15:00 UTC", "Thanks David! I'm putting together a framework for AI audits - happy to share more details if interested."],
        ["conv5", "Lisa Park", "Me", "2024-08-15 15:00:00 UTC", "Congrats on the new role!"],
        ["conv6", "James Wong", "Me", "2023-06-20 09:00:00 UTC", "Great meeting you at the conference! Let's stay in touch."],
    ]

    with open(output_dir / "messages.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(messages)

    # Sample endorsements received
    endorsements = [
        ["Endorser First Name", "Endorser Last Name", "Skill Name"],
        ["Sarah", "Chen", "Python"],
        ["Sarah", "Chen", "Machine Learning"],
        ["Mike", "Torres", "Project Management"],
        ["Mike", "Torres", "Leadership"],
        ["David", "Kim", "AI"],
        ["Chris", "Brown", "Python"],
        ["Chris", "Brown", "AI"],
        ["Chris", "Brown", "Machine Learning"],
    ]

    with open(output_dir / "Endorsement_Received_Info.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(endorsements)

    # Sample recommendations received
    recommendations = [
        ["First Name", "Last Name", "Recommendation"],
        ["Mike", "Torres", "Exceptional technical leadership and strategic thinking. Highly recommend for any AI initiative."],
    ]

    with open(output_dir / "Recommendations_Received.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(recommendations)

    print(f"Sample data generated in: {output_dir}")

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="LinkedIn Network Intelligence")
    parser.add_argument("--data", "-d", type=str, help="Path to LinkedIn export directory")
    parser.add_argument("--example", "-e", action="store_true", help="Run with sample data")
    parser.add_argument("--warm-path", "-w", type=str, help="Find warm path to target company")
    parser.add_argument("--output", "-o", type=str, help="Output directory")
    parser.add_argument("--generate-sample", action="store_true", help="Generate sample data for testing")

    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else Path.cwd() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate sample data
    if args.generate_sample:
        generate_sample_data(output_dir / "sample_linkedin_export")
        return

    # Determine data source
    if args.example:
        # Generate and use sample data
        sample_dir = output_dir / "sample_linkedin_export"
        generate_sample_data(sample_dir)
        data_dir = sample_dir
    elif args.data:
        data_dir = Path(args.data)
    else:
        print("Use --data <path> to analyze your LinkedIn export")
        print("Or --example to run with sample data")
        print("Or --generate-sample to create test data")
        return

    # Parse data
    print(f"Parsing LinkedIn data from: {data_dir}")
    data_parser = LinkedInDataParser(data_dir)
    data_parser.parse_all()

    print(f"Found {len(data_parser.connections)} connections")
    print(f"Found {len(data_parser.messages)} messages")

    # Create analyzer
    analyzer = NetworkAnalyzer(data_parser)

    # Generate reports
    if args.warm_path:
        report = generate_warm_path_report(analyzer, args.warm_path)
        report_path = output_dir / f"warm_path_{args.warm_path.lower().replace(' ', '_')}.md"
    else:
        report = generate_report(analyzer)
        report_path = output_dir / "network_intelligence_report.md"

    report_path.write_text(report)

    print(f"\n{'='*60}")
    print(f"Report generated: {report_path}")
    print(f"{'='*60}\n")
    print(report[:2000] + "\n...\n[Report truncated - see full file]")

if __name__ == "__main__":
    main()
