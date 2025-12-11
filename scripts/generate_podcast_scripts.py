#!/usr/bin/env python3
"""
HB411 Healthy Boundaries for Leaders - Podcast Script Generator

Generates 20-minute podcast scripts (~3000 words) for all 15 weeks of the course.
Uses RAG to pull relevant content from ChromaDB collection "course_hb411".
"""

import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import chromadb
    from chromadb.config import Settings

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("Warning: ChromaDB not available. Will generate scripts without RAG content.")

# =============================================================================
# COURSE STRUCTURE
# =============================================================================

COURSE_STRUCTURE = {
    1: {
        "title": "Introduction to Boundaries",
        "readings": ["Cloud & Townsend Chapter 1"],
        "themes": [
            "What are boundaries",
            "Why boundaries matter",
            "Personal property lines",
            "Spiritual foundations of boundaries",
            "Taking ownership",
        ],
        "key_concepts": [
            "boundaries as property lines",
            "responsibility",
            "ownership",
            "what is mine vs what is yours",
            "spiritual maturity",
        ],
        "reflection_focus": "Identifying where you currently have unclear boundaries",
    },
    2: {
        "title": "Boundary Development",
        "readings": ["Cloud & Townsend Chapter 2", "Tawwab Chapter 1"],
        "themes": [
            "How boundaries develop",
            "Childhood experiences",
            "Family of origin",
            "Attachment and boundaries",
            "Signs you need boundaries",
        ],
        "key_concepts": [
            "developmental stages",
            "bonding",
            "separation",
            "individuation",
            "family patterns",
            "recognizing boundary needs",
        ],
        "reflection_focus": "Understanding your boundary development history",
    },
    3: {
        "title": "Boundary Problems",
        "readings": ["Cloud & Townsend Chapter 3", "Tawwab Chapters 2-3"],
        "themes": [
            "Compliants",
            "Avoidants",
            "Controllers",
            "Nonresponsives",
            "Boundary violations",
            "Types of boundary issues",
        ],
        "key_concepts": [
            "saying yes when you mean no",
            "avoiding intimacy",
            "controlling others",
            "not responding to needs",
            "porous vs rigid boundaries",
        ],
        "reflection_focus": "Identifying your personal boundary problem patterns",
    },
    4: {
        "title": "Laws of Boundaries",
        "readings": ["Cloud & Townsend Chapter 4"],
        "themes": [
            "Law of sowing and reaping",
            "Law of responsibility",
            "Law of power",
            "Law of respect",
            "Law of motivation",
            "Law of evaluation",
        ],
        "key_concepts": [
            "natural consequences",
            "personal responsibility",
            "limits of power",
            "respecting others' boundaries",
            "examining motivations",
        ],
        "reflection_focus": "Which boundary laws do you struggle with most?",
    },
    5: {
        "title": "Myths and Types of Boundaries",
        "readings": ["Cloud & Townsend Chapter 5", "Tawwab Chapter 4"],
        "themes": [
            "Common boundary myths",
            "Boundaries are selfish myth",
            "Boundaries hurt others myth",
            "Physical boundaries",
            "Emotional boundaries",
            "Time boundaries",
        ],
        "key_concepts": [
            "debunking myths",
            "guilt and boundaries",
            "types of boundaries",
            "physical space",
            "emotional protection",
            "time management",
        ],
        "reflection_focus": "What myths about boundaries have held you back?",
    },
    6: {
        "title": "Boundaries and Self Systems I",
        "readings": ["Tawwab Chapters 5-6", "McBride Chapters 1-2"],
        "themes": [
            "Self-care and boundaries",
            "Narcissism in relationships",
            "Self-esteem",
            "Recognizing unhealthy patterns",
            "Beginning the healing journey",
        ],
        "key_concepts": [
            "self-care as boundary",
            "narcissistic relationships",
            "self-worth",
            "pattern recognition",
            "starting recovery",
        ],
        "reflection_focus": "How has your self-worth affected your boundary setting?",
    },
    7: {
        "title": "Boundaries and Self Systems II",
        "readings": ["McBride Chapters 3-4", "Tawwab Chapters 7-8"],
        "themes": [
            "Deeper patterns",
            "Family dynamics",
            "Romantic relationships",
            "Friendship boundaries",
            "Breaking cycles",
        ],
        "key_concepts": [
            "intergenerational patterns",
            "romantic boundary issues",
            "friend boundaries",
            "cycle breaking",
            "new patterns",
        ],
        "reflection_focus": "What relationship patterns do you need to change?",
    },
    8: {
        "title": "Family Boundaries",
        "readings": ["Cloud & Townsend Chapter 6"],
        "themes": [
            "Boundaries with parents",
            "Adult children issues",
            "Extended family",
            "Holiday boundaries",
            "Financial boundaries with family",
        ],
        "key_concepts": [
            "honoring parents with boundaries",
            "adult individuation",
            "family systems",
            "seasonal boundaries",
            "money and family",
        ],
        "reflection_focus": "Where do your family boundaries need work?",
    },
    9: {
        "title": "Ministry and Work Boundaries",
        "readings": ["Cloud & Townsend Chapter 8", "Tawwab Chapter 8"],
        "themes": [
            "Professional boundaries",
            "Ministry burnout",
            "Work-life balance",
            "Saying no professionally",
            "Healthy helping",
        ],
        "key_concepts": [
            "professional limits",
            "compassion fatigue",
            "sustainable ministry",
            "work boundaries",
            "helper syndrome",
        ],
        "reflection_focus": "Are you practicing sustainable ministry/work patterns?",
    },
    10: {
        "title": "Healing and Recovery I",
        "readings": ["McBride Chapters 5-6"],
        "themes": [
            "Grieving losses",
            "Processing pain",
            "Emotional healing",
            "Support systems",
            "Beginning recovery work",
        ],
        "key_concepts": [
            "grief work",
            "emotional processing",
            "healing journey",
            "building support",
            "recovery foundations",
        ],
        "reflection_focus": "What losses related to boundaries do you need to grieve?",
    },
    11: {
        "title": "Healing and Recovery II",
        "readings": ["McBride Chapters 7-8"],
        "themes": [
            "Continued healing",
            "New patterns",
            "Relapse prevention",
            "Building resilience",
            "Moving forward",
        ],
        "key_concepts": [
            "sustained recovery",
            "new habits",
            "preventing backsliding",
            "emotional resilience",
            "future orientation",
        ],
        "reflection_focus": "What does sustained boundary health look like for you?",
    },
    12: {
        "title": "Integration",
        "readings": ["McBride Chapters 9-10", "Cloud & Townsend Chapter 9"],
        "themes": [
            "Putting it together",
            "Boundaries with yourself",
            "Self-discipline",
            "Internal boundaries",
            "Wholeness",
        ],
        "key_concepts": [
            "integration",
            "self-boundaries",
            "internal limits",
            "discipline",
            "holistic health",
        ],
        "reflection_focus": "How will you integrate these learnings into daily life?",
    },
    13: {
        "title": "Spiritual Dimensions of Boundaries",
        "readings": ["Cloud & Townsend Chapter 10"],
        "themes": [
            "God and boundaries",
            "Spiritual growth",
            "Faith and limits",
            "Divine example",
            "Spiritual maturity",
        ],
        "key_concepts": [
            "God's boundaries",
            "spiritual development",
            "faith integration",
            "biblical boundaries",
            "mature spirituality",
        ],
        "reflection_focus": "How does your faith inform your boundary practice?",
    },
    14: {
        "title": "Technology and Self Boundaries",
        "readings": ["Tawwab Chapters 9-10"],
        "themes": [
            "Digital boundaries",
            "Social media limits",
            "Screen time",
            "Online relationships",
            "Technology wellness",
        ],
        "key_concepts": [
            "digital limits",
            "social media boundaries",
            "tech-life balance",
            "online safety",
            "digital wellness",
        ],
        "reflection_focus": "What technology boundaries do you need to establish?",
    },
    15: {
        "title": "Course Conclusion and Integration",
        "readings": ["Integration of all materials"],
        "themes": [
            "Course synthesis",
            "Personal growth plan",
            "Ongoing practice",
            "Community support",
            "Moving forward",
        ],
        "key_concepts": [
            "synthesis",
            "growth planning",
            "practice commitment",
            "accountability",
            "next steps",
        ],
        "reflection_focus": "What is your boundary practice plan going forward?",
    },
}

# =============================================================================
# VOICE CHARACTERS
# =============================================================================

VOICES = {
    "host": {
        "name": "Dr. Sarah Chen",
        "role": "Host & Course Facilitator",
        "style": "Warm, professional, guides conversation",
    },
    "expert": {
        "name": "Rev. Marcus Thompson",
        "role": "Ministry & Pastoral Expert",
        "style": "Thoughtful, practical ministry experience",
    },
    "counselor": {
        "name": "Dr. Elena Rodriguez",
        "role": "Licensed Counselor & Therapist",
        "style": "Empathetic, clinical insights, trauma-informed",
    },
}

# =============================================================================
# RAG CONTENT RETRIEVAL
# =============================================================================


class RAGContentRetriever:
    """Retrieves relevant content from ChromaDB for script generation."""

    def __init__(self, collection_name: str = "course_hb411"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialize()

    def _initialize(self):
        """Initialize ChromaDB connection."""
        if not CHROMA_AVAILABLE:
            return

        try:
            # Try persistent client first
            chroma_path = PROJECT_ROOT / "data" / "chroma"
            if chroma_path.exists():
                self.client = chromadb.PersistentClient(path=str(chroma_path))
            else:
                # Try HTTP client
                self.client = chromadb.HttpClient(host="localhost", port=8000)

            # Get or create collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
                print(f"✓ Connected to ChromaDB collection: {self.collection_name}")
                print(f"  Collection has {self.collection.count()} documents")
            except Exception:
                print(
                    f"Note: Collection '{self.collection_name}' not found. Using template content."
                )
                self.collection = None

        except Exception as e:
            print(f"Note: ChromaDB connection failed ({e}). Using template content.")
            self.client = None
            self.collection = None

    def get_relevant_content(
        self, week: int, themes: List[str], n_results: int = 5
    ) -> List[Dict]:
        """Query ChromaDB for relevant content based on week themes."""
        if not self.collection:
            return []

        results = []
        try:
            # Build query from themes
            query_text = " ".join(themes)

            response = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            if response and response.get("documents"):
                for i, doc in enumerate(response["documents"][0]):
                    metadata = (
                        response["metadatas"][0][i] if response.get("metadatas") else {}
                    )
                    results.append(
                        {
                            "content": doc,
                            "source": metadata.get("source", "Course Materials"),
                            "chapter": metadata.get("chapter", ""),
                            "relevance": (
                                1 - response["distances"][0][i]
                                if response.get("distances")
                                else 0.5
                            ),
                        }
                    )

        except Exception as e:
            print(f"  Warning: RAG query failed for week {week}: {e}")

        return results


# =============================================================================
# SCRIPT GENERATOR
# =============================================================================


class PodcastScriptGenerator:
    """Generates podcast scripts for the HB411 course."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rag = RAGContentRetriever()

    def generate_all_scripts(self):
        """Generate scripts for all 15 weeks."""
        print("\n" + "=" * 60)
        print("HB411 Healthy Boundaries - Podcast Script Generator")
        print("=" * 60)

        for week in range(1, 16):
            print(f"\nGenerating Week {week} script...")
            script = self.generate_week_script(week)
            self.save_script(week, script)

        print("\n" + "=" * 60)
        print("✓ All 15 podcast scripts generated successfully!")
        print(f"  Output directory: {self.output_dir}")
        print("=" * 60)

    def generate_week_script(self, week: int) -> str:
        """Generate a complete podcast script for a given week."""
        week_data = COURSE_STRUCTURE[week]

        # Get RAG content
        rag_content = self.rag.get_relevant_content(
            week, week_data["themes"], n_results=5
        )

        # Build script sections
        script_parts = []

        # Header
        script_parts.append(self._generate_header(week, week_data))

        # Introduction segment
        script_parts.append(self._generate_intro(week, week_data))

        # Main content segments
        script_parts.append(self._generate_main_content(week, week_data, rag_content))

        # Expert discussion
        script_parts.append(
            self._generate_expert_discussion(week, week_data, rag_content)
        )

        # Practical application
        script_parts.append(self._generate_practical_section(week, week_data))

        # Reflection questions
        script_parts.append(self._generate_reflection_section(week, week_data))

        # Closing
        script_parts.append(self._generate_closing(week, week_data))

        return "\n\n".join(script_parts)

    def _generate_header(self, week: int, week_data: Dict) -> str:
        """Generate script header with metadata."""
        return f"""{'='*70}
HB411 HEALTHY BOUNDARIES FOR LEADERS
WEEK {week}: {week_data['title'].upper()}
{'='*70}

PODCAST SCRIPT
Duration: ~20 minutes (~3000 words)
Generated: {datetime.now().strftime('%Y-%m-%d')}

READINGS FOR THIS WEEK:
{chr(10).join(f'  • {r}' for r in week_data['readings'])}

KEY THEMES:
{chr(10).join(f'  • {t}' for t in week_data['themes'])}

VOICE CAST:
  • {VOICES['host']['name']} - {VOICES['host']['role']}
  • {VOICES['expert']['name']} - {VOICES['expert']['role']}
  • {VOICES['counselor']['name']} - {VOICES['counselor']['role']}

{'='*70}
SCRIPT BEGINS
{'='*70}
"""

    def _generate_intro(self, week: int, week_data: Dict) -> str:
        """Generate introduction segment."""

        # Week-specific intro hooks
        intro_hooks = {
            1: "Have you ever felt like people keep walking all over you? Or maybe you've been told you're too rigid, too closed off? Today we're starting a journey that will transform how you understand yourself and your relationships.",
            2: "Where did your boundary patterns come from? The answer might surprise you—and understanding it is the first step toward lasting change.",
            3: "Some of us say yes when we desperately want to say no. Others build walls so high no one can get in. Today we're getting honest about our boundary problems.",
            4: "What if I told you there are actual laws—principles that govern how boundaries work? Understanding these can revolutionize your relationships.",
            5: "Setting boundaries is selfish. Boundaries hurt relationships. If I were really spiritual, I wouldn't need boundaries. Sound familiar? Let's bust some myths.",
            6: "Your sense of self directly impacts your ability to set boundaries. Today we explore the deep connection between who you are and the limits you set.",
            7: "Family patterns. Romantic relationships. Friendships. Each requires different boundary skills—and each can trigger our deepest wounds.",
            8: "Holidays approaching? Dreading that family gathering? You're not alone. Family boundaries are often the hardest—and most important—to navigate.",
            9: "Ministry burnout. Work exhaustion. The helper who can't help themselves. If you serve others professionally, this episode is essential listening.",
            10: "Healing isn't linear. Today we begin the deep work of grieving what was lost and finding our way toward wholeness.",
            11: "Recovery is possible. New patterns can be established. Today we continue our healing journey with hope and practical tools.",
            12: "We've covered so much ground. Now comes the crucial work of putting it all together into a sustainable practice.",
            13: "What does God have to say about boundaries? The answer may be more affirming than you expect.",
            14: "Our phones never leave us alone. Social media demands constant attention. Digital boundaries are the frontier of modern boundary work.",
            15: "We've journeyed far together. Today we celebrate growth, solidify learning, and chart the path forward.",
        }

        return f"""[SEGMENT 1: INTRODUCTION - 3 minutes]
[MUSIC: Theme music fades in, warm and welcoming]

[VOICE: {VOICES['host']['name']}]

Welcome back to Healthy Boundaries for Leaders, the podcast companion to HB411. I'm {VOICES['host']['name']}, and I'm so glad you're here for Week {week}: {week_data['title']}.

{intro_hooks.get(week, "This week we're diving into crucial concepts that will deepen your understanding of boundaries.")}

This week's readings include {', '.join(week_data['readings'])}. If you haven't had a chance to complete the readings yet, don't worry—this podcast will give you the key insights, though I do encourage you to engage with the full texts when you can.

Joining me today, as always, are my wonderful co-hosts: {VOICES['expert']['name']}, bringing the ministry and pastoral perspective, and {VOICES['counselor']['name']}, our licensed counselor who helps us understand the psychological dimensions.

[VOICE: {VOICES['expert']['name']}]

Great to be here, Sarah. Week {week} is one I've been looking forward to because {week_data['title'].lower()} touches so many people in ministry.

[VOICE: {VOICES['counselor']['name']}]

Absolutely. In my practice, I see these themes come up constantly. The concepts we'll cover today—{', '.join(week_data['key_concepts'][:3])}—these are foundational to healthy functioning.

[VOICE: {VOICES['host']['name']}]

Let's dive in. Remember, you can pause at any time if you need to reflect or take notes. This journey is yours, and there's no rushing it.

[MUSIC: Theme music fades out]
"""

    def _generate_main_content(
        self, week: int, week_data: Dict, rag_content: List[Dict]
    ) -> str:
        """Generate main content segment with concepts and teaching."""

        # Generate theme-specific content
        theme_content = self._expand_themes(week, week_data)

        # Integrate RAG content if available
        rag_integration = ""
        if rag_content:
            excerpts = []
            for i, content in enumerate(rag_content[:3]):
                if content.get("content"):
                    # Clean and excerpt the content
                    text = content["content"][:500].strip()
                    if len(content["content"]) > 500:
                        text += "..."
                    source = content.get("source", "Course Materials")
                    excerpts.append(f'From our readings: "{text}"\n—{source}')

            if excerpts:
                rag_integration = f"""
[VOICE: {VOICES['host']['name']}]

Let me share a powerful passage from this week's readings:

{excerpts[0]}

[VOICE: {VOICES['counselor']['name']}]

That really captures something essential. In therapy, we often see people struggling with exactly this dynamic.
"""

        # Week-specific case studies and examples
        case_studies = {
            1: """Let me share a story that illustrates this. A pastor named James came to counseling exhausted. He was on call 24/7, answering every text, attending every hospital visit, saying yes to every meeting. When asked who else could share these responsibilities, he said, "No one. They need me."

But here's what James discovered: by having no boundaries, he wasn't actually serving his congregation better—he was serving them worse. His sermon preparation suffered. His presence at home with his family disappeared. His spiritual life evaporated. The very things that made him a good pastor were being sacrificed on the altar of availability.

When James finally started setting limits—office hours, a true Sabbath, boundaries around his phone—something remarkable happened. His congregation rose to meet the challenge. Lay leaders stepped up. People learned to wait. And James became a better pastor, not by doing more, but by doing less sustainably.""",
            2: """Consider Maria's story. Growing up, Maria's mother had severe anxiety. The only way Maria could feel safe was to anticipate her mother's moods and manage them. She became exquisitely attuned to others' emotions—so attuned that she lost track of her own.

As an adult, Maria was everyone's confidant, everyone's helper, everyone's support. People loved being around her because she always made them feel better. But inside, Maria was empty. She'd never developed the capacity to know what she needed because her energy had always gone to knowing what others needed.

Maria's boundary work started with a simple question: "What do I feel right now?" She had to learn something most people take for granted—the ability to identify her own emotions and needs. This is what damaged boundary development looks like: not knowing where you end and others begin.""",
            3: """Let me describe four people I've worked with:

Tom says yes to everything and then seethes with resentment. He agrees to lead another committee, host another event, take on another project—and then complains about how busy he is. That's the Compliant.

Susan can't ask for help. She's been sick for weeks but won't tell anyone. She struggles in silence, convinced that having needs makes her a burden. She's dying of loneliness while surrounded by people who would help if she asked. That's the Avoidant.

Richard tells everyone what to do and gets furious when they don't comply. He can't understand why people don't appreciate his "help" and "guidance." He runs roughshod over others' preferences while claiming he's doing it for their good. That's the Controller.

And Linda? Linda is checked out. Her husband is struggling, her kids are acting out, her coworkers are drowning—and Linda just... isn't there. She's physically present but emotionally absent. She's not mean, she's just uninvolved. That's the Nonresponsive.

Most of us can find ourselves in these descriptions. The question is: which pattern causes you the most trouble?""",
            4: """The Law of Sowing and Reaping changed everything for one mother I counseled. Her adult son kept making poor financial decisions, and she kept bailing him out. Every few months, another crisis, another check.

When she learned about natural consequences, she made a painful decision: no more rescues. The next time her son called with a financial emergency, she said, "I love you, and I'm not going to help with money anymore. I believe you can figure this out."

Her son was furious. He didn't figure it out right away—he struggled for months. But eventually, for the first time in his adult life, he learned to manage money. Not because his mother lectured him, but because reality taught him. The mother's boundaries, as painful as they were to set, were the most loving thing she could have done.

That's the Law of Sowing and Reaping: allowing people to experience the consequences of their choices. Not punishment—reality.""",
            5: """The myth that hurt Emily most was "If I set boundaries, people will abandon me." This belief came from childhood, when her love was indeed conditional on compliance. Set a boundary, lose the relationship—that was the unspoken rule.

As an adult, Emily tested this belief. She started setting small boundaries—declining an invitation, expressing a preference, saying "I need time to think about that" instead of immediately agreeing. And you know what happened?

Some people left. That was hard but clarifying. Those relationships were built on Emily's compliance, not on mutual respect.

But many people stayed. And those relationships deepened. Emily discovered that the people who could handle her boundaries were the people worth keeping. The myth was only partially true: boundaries do cost some relationships, but they cost the wrong relationships while making space for the right ones.""",
            6: """The link between self-worth and boundaries is painfully clear in Daniel's story. Daniel grew up as the scapegoat in a narcissistic family system. Everything that went wrong was Daniel's fault. He internalized the message: you're bad, you're wrong, you don't deserve good things.

As an adult, Daniel accepted treatment no one with healthy self-esteem would accept. He stayed in abusive relationships. He took jobs far below his capability. He let people walk all over him because deep down, he believed he deserved it.

Daniel's boundary work couldn't start with boundaries—it had to start with self-worth. He had to believe he was worth protecting before he could protect himself. Therapy focused first on challenging his core beliefs about himself. Only then could boundary work take root.

If you struggle to set boundaries, ask yourself: Do I believe I'm worth protecting? If the answer is no, that's where the work begins.""",
            7: """Generational patterns are powerful. Take the Chen family. In each generation, the oldest daughter sacrificed herself for the family. Great-grandmother worked to put her brothers through school. Grandmother raised her siblings when their mother died. Mother gave up her career for her siblings' children. And now, the current generation's oldest daughter was being groomed for the same role.

When this young woman—a medical student—started setting boundaries, the family system erupted. She was accused of abandoning tradition, dishonoring her family, being selfish. The pressure was immense.

But she held firm. She completed medical school. She didn't sacrifice her future for relatives who could help themselves. And in doing so, she broke a cycle that had constrained women in her family for generations.

Sometimes the most loving thing you can do for your family is stop the pattern—even when they call it betrayal.""",
            8: """Let me tell you about holiday boundaries in action. The Kim family had a tradition: everyone gathered at Mom's house for a week at Christmas. Everyone meant everyone—twenty people in a four-bedroom house, with all the stress you'd imagine.

One year, Sarah Kim announced she wasn't coming. She and her husband and kids would spend Christmas at home, visiting Mom for a day on December 26th.

The response was nuclear. Sarah was accused of destroying the family, ruining Christmas, not caring about tradition. Her mother cried. Her siblings guilted. Everyone predicted doom.

And then Christmas came. Sarah had a peaceful holiday. Her kids opened presents in their pajamas. She and her husband relaxed for the first time in years. The visit on the 26th was actually pleasant because Sarah wasn't exhausted and resentful.

The next year, two of Sarah's siblings did the same thing. The tradition evolved. It didn't disappear—it adapted. And the family survived just fine.

Family traditions are only sacred if they serve the family. When they harm the family, they deserve to change.""",
            9: """Compassion fatigue hit Pastor Williams hard. Twenty years of ministry—twenty years of being available, absorbing others' pain, carrying burdens that weren't his to carry. By year twenty, he was numb. He couldn't feel joy. He went through the motions of ministry but felt nothing.

In counseling, Pastor Williams made a discovery: he'd confused boundaries with abandonment. In his mind, setting limits meant failing the people he served. So he set no limits—and destroyed his capacity to serve at all.

His recovery required radical change: real days off, supervision for pastoral care, delegation of responsibilities, and something revolutionary—hobbies. Pastor Williams hadn't done something purely for enjoyment in decades.

Two years later, he describes himself as "a completely different pastor—and a much better one." Not because he does more, but because he finally learned that sustainable ministry requires sustainable ministers.""",
            10: """Grief work doesn't follow a schedule. Patricia thought she was "over" her childhood by age forty. She'd been in therapy, done the work, moved on. But when she started intensive boundary work, the grief came flooding back.

She grieved the mother she should have had. She grieved the protection she never received. She grieved the boundaries that were violated and the ones she was never taught to set. She grieved the years spent in damaging relationships because she didn't know another way.

This grief wasn't regression—it was progression. Patricia was grieving at a deeper level because she'd grown enough to access deeper levels. Each layer of healing reveals the next layer of pain. That's not failure; that's how healing works.

If grief surprises you during this course, let it come. It means the work is working.""",
            11: """Recovery isn't linear. Michael had six months of boundary progress—setting limits at work, speaking up in relationships, honoring his own needs. Then his mother got sick, and everything collapsed. He found himself in old patterns: over-functioning, neglecting himself, saying yes to everything.

Michael thought he'd failed. But his therapist reframed it: "You didn't fail—you got data. Now you know that family health crises are a trigger. Now you can prepare."

Michael developed a crisis protocol: automatic boundaries that kick in when he's stressed. He gave his spouse permission to remind him of his limits. He scheduled non-negotiable self-care even in emergencies.

The next crisis—and there's always a next crisis—Michael handled differently. Not perfectly, but differently. That's recovery: not the absence of struggle, but improved response to struggle.""",
            12: """Integration means making boundaries second nature. When someone asks for your time, you don't have to think through a complicated framework—you just know if you can give it or not. When someone violates your limits, you notice immediately, not days later.

This kind of integration takes time. Years, often. But there are signs of progress:

You catch yourself before the boundary violation, not just after.
You set limits without excessive guilt.
You receive "no" from others without taking it personally.
You trust your own perceptions about what you need.
You can be connected and separate at the same time.

These markers aren't destinations—they're directions. You're moving toward them, even when progress feels slow.""",
            13: """The intersection of faith and boundaries transformed Pastor Rivera's ministry. For years, he'd believed that Christian service meant unlimited availability. His theology supported his workaholism.

But then he studied Jesus more carefully. He noticed Jesus withdrawing to pray. He noticed Jesus limiting his accessibility. He noticed Jesus saying no to legitimate requests. He noticed Jesus' boundary with Peter: "Get behind me, Satan."

Pastor Rivera realized his theology of boundaries wasn't too biblical—it wasn't biblical enough. A more careful reading of Scripture revealed a God who respects limits, expects limits, and models limits.

Now, when Pastor Rivera teaches about boundaries, he teaches them as spiritual disciplines. Not as accommodations to human weakness, but as practices of mature faith.""",
            14: """Digital boundaries saved Rachel's mental health. At her worst, Rachel was on her phone six hours a day—not for work, but for scrolling. She'd start the day with social media and end it the same way. Her attention was constantly fragmented. Her mood tracked her notifications.

Rachel implemented boundaries gradually. First, no phones in the bedroom. Then, no social media before 9 AM. Then, app time limits. Then, scheduled "phone-free" hours during the day.

The first week was brutal. Rachel felt phantom vibrations, constant urges to check. But by week four, something shifted. She noticed trees. She had thoughts that weren't interrupted. She read a book—an actual, physical book—for the first time in years.

Rachel didn't quit technology. She just stopped letting it run her life. That required boundaries—real, enforced, uncomfortable boundaries.""",
            15: """Fifteen weeks of learning means nothing without implementation. Let me tell you about two people who took this course.

Person A learned all the concepts, passed all the quizzes, could recite the material perfectly. But they never actually set a boundary. A year later, their life was exactly the same.

Person B struggled with the concepts but practiced constantly. They set small boundaries, failed, adjusted, tried again. A year later, their relationships were transformed.

Knowledge without practice is just information. The gap between knowing about boundaries and living with boundaries is bridged only by action—imperfect, repeated, courageous action.

As we close this course, the question isn't "What did you learn?" The question is "What will you do?"
""",
        }

        return f"""[SEGMENT 2: CORE CONCEPTS - 8 minutes]

[VOICE: {VOICES['host']['name']}]

Let's unpack the core concepts from this week's readings. {week_data['title']} might sound straightforward, but there's real depth here that we need to explore together.

{theme_content}
{rag_integration}

{case_studies.get(week, "")}

[VOICE: {VOICES['expert']['name']}]

You know, Sarah, in my years of ministry, I've seen how {week_data['themes'][0].lower()} affects not just individuals but entire communities. When leaders don't understand these principles, it ripples outward. Churches, organizations, families—they all suffer when boundaries aren't understood.

[VOICE: {VOICES['counselor']['name']}]

That's such an important point, Marcus. The research supports this too. Studies show that leaders with healthy boundary awareness create healthier organizational cultures. It's not just personal—it's systemic. Your individual boundary work has collective implications.

[VOICE: {VOICES['host']['name']}]

That systemic element is crucial. We're not just doing this work for ourselves. The boundaries we model shape what others believe is possible. Our children watch us. Our colleagues observe us. Our congregations learn from us.

Let's look at each of this week's key concepts in more depth:

**{week_data['key_concepts'][0].title()}**

This foundational idea helps us understand that boundaries aren't walls—they're more like property lines. They define where you end and others begin. Without this clarity, we lose ourselves in relationships or become isolated from meaningful connection. Think about it: when you know where your property ends, you can be a good neighbor. You know what's yours to tend and what belongs to someone else. The same is true emotionally.

**{week_data['key_concepts'][1].title()}**

Building on that foundation, we see how {week_data['key_concepts'][1]} connects to our ability to function in relationships. This isn't about being rigid or harsh—it's about having clear enough boundaries that we can actually be present with others. Paradoxically, good boundaries enable deeper intimacy. When I know where I end, I can truly encounter where you begin.

**{week_data['key_concepts'][2].title()}**

And here's where it gets practical. Understanding {week_data['key_concepts'][2]} gives us tools we can actually use in daily life. This is where the rubber meets the road. Theory is important, but transformation happens in the moments when we actually apply what we're learning.

[VOICE: {VOICES['expert']['name']}]

What I appreciate about this week's readings is how they connect theory to practice. It's not enough to understand boundaries intellectually—we have to live them. Head knowledge becomes heart knowledge through practice.

[VOICE: {VOICES['counselor']['name']}]

And that practice often feels uncomfortable at first. I tell my clients: if boundary-setting felt easy, you'd already be doing it. The discomfort is actually a sign that you're growing into new territory.
"""

    def _expand_themes(self, week: int, week_data: Dict) -> str:
        """Generate expanded content for the week's themes."""

        theme_expansions = {
            1: """Understanding boundaries begins with a simple but profound question: What is mine to take care of, and what belongs to someone else? Cloud and Townsend use the metaphor of property lines—those markers that show where your yard ends and your neighbor's begins. Without clear property lines, chaos ensues. The same is true in relationships.

Think about it this way: You're responsible for your own thoughts, feelings, choices, and behaviors. You're not responsible for someone else's thoughts, feelings, choices, or behaviors. This seems obvious when stated plainly, but in practice? We violate this principle constantly.""",
            2: """Boundaries don't appear out of nowhere. They develop—or fail to develop—through our earliest relationships. From the moment we're born, we're learning: Is the world safe? Can I trust my needs will be met? Am I allowed to be separate from my caregivers?

Healthy boundary development follows a predictable pattern: bonding (connection), separation (individuation), and integration (maintaining connection while being separate). When any stage is disrupted, we carry those wounds forward.""",
            3: """Let's get honest about boundary problems. Cloud and Townsend identify several types: the Compliant (says yes when they mean no), the Avoidant (can't ask for help or receive), the Controller (doesn't respect others' boundaries), and the Nonresponsive (fails to respond to others' needs).

Most of us can see ourselves in more than one category. That's normal. The goal isn't perfection—it's awareness.""",
            4: """The Law of Sowing and Reaping tells us that our actions have consequences—and we should let people experience the consequences of their behavior. When we constantly rescue others from natural consequences, we rob them of growth opportunities.

The Law of Responsibility clarifies what we are and aren't responsible for. The Law of Power helps us understand what we can and cannot change. These aren't arbitrary rules—they're descriptions of how reality works.""",
            5: """Myth: Boundaries are selfish.
Reality: Boundaries are essential for genuine love. You cannot give what you don't have, and you cannot have yourself if you have no boundaries.

Myth: If I set boundaries, I'll lose relationships.
Reality: You may lose unhealthy relationships. Healthy relationships can handle boundaries—in fact, they require them.

Myth: Spiritual people don't need boundaries.
Reality: God has boundaries. Jesus had boundaries. Boundaries are part of mature faith.""",
            6: """Here's a truth that might sting: The quality of your boundaries reflects the quality of your relationship with yourself. When self-esteem is low, we accept treatment we shouldn't. When we don't value ourselves, we don't protect ourselves.

The work of boundaries is intertwined with the work of self-worth. You cannot separate them.""",
            7: """Family systems theory shows us that patterns repeat across generations. The boundary problems you struggle with likely have roots in your family of origin—and without intervention, you'll pass them on.

In romantic relationships, boundary violations often masquerade as love. "They're just jealous because they love me." "They need to know where I am at all times because they care." No. That's not love. That's control.""",
            8: """Family boundaries are complicated by love, history, and often guilt. The commandment to honor your parents doesn't mean having no boundaries with them. Honor and boundaries can coexist.

Adult children must individuate—become separate adults—to have healthy relationships with parents. This doesn't mean cutting off. It means having your own values, making your own decisions, and not needing parental approval for every choice.""",
            9: """Ministry and helping professions attract people with boundary issues. We're drawn to serving others, sometimes because we learned that's how to earn love, sometimes because focusing on others lets us avoid our own pain.

Sustainable ministry requires sustainable boundaries. You cannot pour from an empty cup. Taking care of yourself isn't selfish—it's strategic. It's what allows you to keep serving over the long haul.""",
            10: """Healing requires grieving. We must mourn what we lost—the childhood we didn't have, the relationship that wasn't healthy, the years we spent with poor boundaries. This isn't self-pity. It's necessary emotional processing.

Grief work isn't optional. What we don't grieve, we carry. And what we carry shapes everything we do.""",
            11: """Recovery isn't a destination—it's a direction. There will be setbacks. Old patterns will reassert themselves, especially under stress. This is normal. The question isn't whether you'll struggle but how you'll respond when you do.

Building resilience means developing multiple supports: therapy, community, spiritual practices, self-care routines. Recovery that depends on one thing is fragile.""",
            12: """Integration means making these concepts part of who you are, not just things you know. It means catching yourself before the boundary violation, not just after. It means having new patterns feel natural, not forced.

Boundaries with yourself—self-discipline, follow-through, keeping promises to yourself—are often the hardest but most important boundaries to maintain.""",
            13: """Does God have boundaries? Absolutely. God respects human choice (free will). God doesn't force relationship. God experiences consequences when we sin (grief). God says no to certain behaviors.

If God—perfect, loving, all-powerful God—has boundaries, surely we're allowed to have them too. Boundaries aren't a failure of faith. They're an expression of it.""",
            14: """Our digital lives need boundaries as much as our physical lives. Social media creates false intimacy and comparison traps. Constant connectivity erodes presence. The attention economy is designed to exploit our vulnerabilities.

What would healthy technology boundaries look like for you? Screen-free times? Social media limits? Email boundaries?""",
            15: """Fifteen weeks. We've covered so much ground: what boundaries are, how they develop, what goes wrong, how to heal, and how to maintain healthy boundaries over time.

The question now is: What will you do with what you've learned? Knowledge without application is just information. The real work begins when the course ends.""",
        }

        return theme_expansions.get(
            week,
            f"This week focuses on {week_data['title'].lower()}, exploring {', '.join(week_data['themes'][:3])}.",
        )

    def _generate_expert_discussion(
        self, week: int, week_data: Dict, rag_content: List[Dict]
    ) -> str:
        """Generate expert discussion segment."""

        # Week-specific ministry stories
        ministry_stories = {
            1: "I remember counseling a pastor who hadn't taken a real day off in three years. Three years! And he wondered why he was struggling. His boundaries weren't just poor—they were nonexistent. He thought self-sacrifice meant self-destruction.",
            2: "Last month, I worked with a church leader who realized her people-pleasing went back to age seven, when she learned that keeping mom happy was the only way to feel safe. Forty years later, she was still living that pattern with her congregation.",
            3: "I've seen entire church boards made up of Compliants—people who said yes to everything, never pushed back, and then burned out simultaneously. The aftermath was devastating. Understanding these patterns isn't just personal—it's organizational.",
            4: "A youth pastor once told me he felt responsible for every kid in his program—their grades, their family situations, everything. When I asked him to list what was actually his responsibility versus God's, he wept. The weight he'd been carrying wasn't his to carry.",
            5: "The guilt around boundaries in ministry is real. I had a senior pastor tell me that setting boundaries felt like abandoning his flock. We had to reframe it: 'A dead shepherd can't protect anyone.'",
            6: "I counseled a worship leader whose entire identity was tied to how the congregation responded on Sunday. Good response? She felt worthy. Flat morning? She spiraled. Her self-esteem was completely externalized.",
            7: "Family systems show up everywhere in church. I worked with a team where the lead pastor unconsciously recreated his family dynamics—the same roles, the same conflicts, the same patterns. Until he saw it, he couldn't change it.",
            8: "Holiday seasons are when pastoral boundaries get tested most. The pressure to be available, to visit every family, to make everyone's Christmas meaningful—it's unsustainable. I've seen too many December burnouts.",
            9: "Compassion fatigue is real. I've walked alongside ministers who gave everything to their congregations and had nothing left for their families. That's not faithfulness—that's a boundary crisis.",
            10: "Healing in ministry often means grieving the pastor you thought you'd be—the one who never got tired, never needed help, never said no. That idealized image has to die for the real you to live.",
            11: "Recovery for ministry leaders looks different. The public nature of the role means you can't hide. I've helped pastors build 'recovery teams'—small groups of trusted people who hold them accountable to sustainable patterns.",
            12: "Integration is where faith and psychology meet beautifully. The internal work of boundaries—self-discipline, self-honesty, self-care—mirrors spiritual formation. They're not separate journeys.",
            13: "I've had fascinating conversations with pastors about God's boundaries. When you see that Jesus said no, withdrew to pray, and limited his accessibility, it changes everything about how you view your own limits.",
            14: "Digital boundaries are the new frontier for ministry. Pastors who are reachable 24/7 via text, social media, and email—they're not more faithful, they're more fragmented. Presence requires absence.",
            15: "Fifteen weeks is just the beginning. The real work happens in the daily choices, the small moments when you choose yourself and trust that's not selfish—it's sustainable.",
        }

        # Week-specific clinical insights
        clinical_insights = {
            1: "From a psychological perspective, boundaries are actually about self-differentiation—the ability to maintain your sense of self while in relationship with others. Without this, we either lose ourselves in relationships or avoid them entirely.",
            2: "The research on attachment is clear: insecure attachment in childhood predicts boundary difficulties in adulthood. But here's the good news—attachment patterns can be 'earned' through later relationships and therapy. Change is possible.",
            3: "The Compliant-Controller dynamic is fascinating clinically. Often, Compliants attract Controllers and vice versa. It's a dance that feels familiar to both, even though it's destructive. Recognition is the first step to interrupting the pattern.",
            4: "Natural consequences are one of the most powerful therapeutic tools we have. When we allow people to experience the results of their choices, we're respecting their agency. Rescuing actually communicates disrespect.",
            5: "Cognitive behavioral therapy works well with boundary myths because they're essentially cognitive distortions. 'I must be available always' is an irrational belief. When we examine it, it crumbles under scrutiny.",
            6: "The link between self-esteem and boundaries is bidirectional. Poor boundaries erode self-esteem, and low self-esteem makes it harder to set boundaries. Intervention at either point can start a positive cycle.",
            7: "Genograms—those family maps we use in therapy—almost always reveal boundary patterns across generations. When clients see the visual, the intergenerational transmission becomes undeniable. And recognizable patterns become changeable patterns.",
            8: "Family systems theory tells us that when one person changes, the system pushes back. Expect resistance when you start setting new boundaries with family. It doesn't mean you're wrong—it means the system is adjusting.",
            9: "Helping professions have the highest rates of burnout precisely because boundaries are chronically violated. The selection process attracts boundary-challenged individuals, and the work environment rewards boundary violations. It's a perfect storm.",
            10: "Grief work is non-negotiable in boundary healing. What's not grieved gets acted out. The anger, sadness, and loss have to go somewhere—either into conscious processing or into symptoms and relationship patterns.",
            11: "Neuroplasticity research gives us hope. The brain can change at any age. New boundary patterns literally create new neural pathways. It's hard at first—you're building a road where there was only forest—but it gets easier.",
            12: "Internal boundaries are fascinating clinically. The ability to delay gratification, keep promises to yourself, manage impulses—these predict success in every domain of life. They're the foundation for external boundaries.",
            13: "Spirituality and mental health are increasingly recognized as interconnected. Clients with healthy spiritual lives often have better outcomes. Boundaries and faith both require trust—trust in yourself, trust in others, trust in something larger.",
            14: "We're seeing a new diagnostic category emerge around technology use. The dopamine hijacking of social media mimics addiction pathways. Digital boundaries aren't optional anymore—they're essential for mental health.",
            15: "Integration in therapy means making the implicit explicit, the unconscious conscious. The same applies to boundary work. When you can articulate your patterns, name them, and recognize them in real-time, you've integrated the learning.",
        }

        return f"""[SEGMENT 3: EXPERT DISCUSSION - 5 minutes]

[VOICE: {VOICES['host']['name']}]

Let's hear from our experts. Marcus, from your ministry experience, what stands out to you about this week's material on {week_data['title'].lower()}?

[VOICE: {VOICES['expert']['name']}]

You know, Sarah, I think about {week_data['themes'][0].lower()} constantly in pastoral work. So many ministry leaders struggle here. They give and give until there's nothing left, thinking that's what faithfulness requires. But that's not biblical—that's burnout waiting to happen.

{ministry_stories.get(week, "")}

[VOICE: {VOICES['counselor']['name']}]

That resonates deeply with what I see clinically. There's often a hero complex underneath poor boundaries—this belief that we have to save everyone, that taking care of ourselves means abandoning others.

{clinical_insights.get(week, "")}

{week_data['key_concepts'][0].title()} connects to attachment patterns formed early in life. If you learned that your worth depended on meeting others' needs, setting boundaries feels like risking abandonment. But here's the truth: people who can't handle your boundaries can't handle your wholeness.

[VOICE: {VOICES['host']['name']}]

That's powerful. "People who can't handle your boundaries can't handle your wholeness." Can you say more about that?

[VOICE: {VOICES['counselor']['name']}]

When you set a boundary, you're essentially saying, "I'm a separate person with my own needs and limits." Some people will find that threatening. They preferred the version of you that was always available, always accommodating, always saying yes.

The loss of those relationships is real and painful. But what you're gaining is the possibility of genuine relationships—ones based on mutual respect rather than your depletion.

Here's what I tell my clients: The people who leave when you set boundaries were only there for what you gave them. The people who stay when you set boundaries are there for who you are. That's a trade worth making, even when it hurts.

[VOICE: {VOICES['expert']['name']}]

In faith terms, we'd say you're exchanging counterfeit intimacy for genuine community. It's a hard trade in the short term, but it's the only path to actual connection. Scripture is full of this pattern—letting go of the false to grasp the true.

Jesus himself modeled this. He withdrew from crowds who wanted more from him. He said no to legitimate requests. He maintained his sense of mission even when others wanted him to be something else. If the Son of God needed boundaries, surely we do too.

[VOICE: {VOICES['host']['name']}]

This connects beautifully to {week_data['reflection_focus'].lower()}. Elena, how would you encourage listeners to approach that reflection?

[VOICE: {VOICES['counselor']['name']}]

Start with curiosity rather than judgment. Notice your patterns without immediately trying to fix them. Ask yourself: Where did I learn this? What was this pattern trying to protect me from? Who modeled this for me? Understanding the origin often softens our self-criticism.

The goal isn't to blame anyone—not your parents, not your church, not yourself. The goal is understanding. With understanding comes choice. And with choice comes freedom.

[VOICE: {VOICES['expert']['name']}]

And remember, awareness is the first step. You can't change what you won't see. Be gentle with yourself as you look at hard things. This work takes courage. The fact that you're here, listening, engaging—that already shows courage.
"""

    def _generate_practical_section(self, week: int, week_data: Dict) -> str:
        """Generate practical application segment."""

        exercises = {
            1: "This week, keep a boundary journal. Every time you say yes when you want to say no—or say no when you wish you could say yes—write it down. Note the situation, what you did, and how you felt. Don't judge, just observe.",
            2: "Draw your family boundary map. Who in your family had healthy boundaries? Who had poor ones? What messages did you receive about boundaries growing up? This isn't about blame—it's about understanding.",
            3: "Take the boundary styles assessment in Tawwab's book. Be honest with yourself. Then pick one specific situation where you'd like to respond differently. Plan what you'll say. Practice it out loud.",
            4: "Identify one situation where you're shielding someone from natural consequences. Ask yourself: Is my 'helping' actually helping? Or am I preventing their growth while exhausting myself?",
            5: "Write down every boundary myth you've believed. Next to each, write the truth that counters it. Post this somewhere you'll see it daily. Repetition rewires belief.",
            6: "Complete the self-esteem inventory in McBride's book. Then write yourself a letter of compassion—addressing yourself as you would a dear friend who was struggling.",
            7: "Map your relationship patterns. In romantic relationships, friendships, and family, what roles do you tend to play? Caretaker? Rescuer? Martyr? Awareness of patterns is the first step to changing them.",
            8: "Before your next family interaction, prepare. What boundaries might be tested? What will you say? How will you stay grounded? Having a plan reduces reactivity.",
            9: "Audit your work/ministry boundaries. Track your hours for one week. Note when you say yes reluctantly. Identify one boundary you'll implement immediately.",
            10: "Create a grief ritual. This might be writing a letter to your younger self, creating art about your losses, or simply setting aside time to feel what you've been avoiding.",
            11: "Build your resilience toolkit. List five healthy coping strategies you'll use when stressed. Identify three people you can call when struggling. Know your warning signs.",
            12: "Write your personal boundaries manifesto. What do you believe about boundaries now? What commitments are you making to yourself? Make it concrete and specific.",
            13: "Reflect on spiritual models of boundaries. Where do you see God setting limits in Scripture? How might your faith support your boundary practice?",
            14: "Conduct a digital boundary audit. Track your screen time. Notice how different platforms make you feel. Set one new technology boundary and keep it for two weeks.",
            15: "Create your ongoing boundary practice plan. What daily, weekly, and monthly practices will support your boundary health? Who will hold you accountable?",
        }

        # Detailed how-to for each exercise
        exercise_details = {
            1: """Here's how to do this practically: Get a small notebook or use your phone's notes app. Create three columns: Situation, Response, and Feeling. 
            
Every time a boundary moment comes up—someone asks for your time, someone pushes your limits, someone needs something from you—record it. Don't wait until the end of the day; capture it in the moment if possible.

At the end of the week, review your entries. Look for patterns. Are certain people always in your journal? Are certain times of day worse? Are certain types of requests harder?

This data is gold. It's not about judging yourself—it's about seeing clearly what's actually happening in your boundary life.""",
            2: """Grab a large piece of paper. Draw yourself in the center. Then add family members around you—parents, siblings, grandparents, any significant figures.

Now draw the boundaries between each person. Thick lines for rigid boundaries. Dotted lines for porous ones. Normal lines for healthy ones. Where are the violations? Where is the enmeshment?

Then, if you can, do the same map for your parents' generation. And their parents. See if patterns emerge across generations. This isn't about blame—it's about recognizing what was passed down unconsciously.

Consider sharing this map with a therapist, counselor, or trusted friend. Sometimes others see patterns we can't see ourselves.""",
            3: """The boundary styles assessment helps you identify whether you tend toward rigid, porous, or healthy boundaries in different areas of your life.

Once you've identified your style, pick one specific situation this week—maybe a conversation with a particular person or a recurring scenario—where you want to respond differently.

Script it out. Literally write what you'll say: "When you ask me to stay late without notice, I feel stressed because I need to honor my family commitments. Going forward, I need 24-hour notice for schedule changes."

Then practice. Say it out loud. Say it in the mirror. Say it to a friend. The more familiar the words feel in your mouth, the more likely you are to actually use them.""",
            4: """Think about one person in your life who consistently experiences negative consequences but somehow those consequences never quite land on them. They bounce to you instead.

Maybe you cover for someone's mistakes at work. Maybe you pay for a family member's poor financial decisions. Maybe you absorb emotional fallout that isn't yours.

Ask yourself: If I stopped intervening, what would naturally happen? Sometimes we're so busy rescuing that we haven't even imagined what not-rescuing would look like.

Then, this week, try one small non-rescue. Let one consequence land where it should. Observe what happens—both externally and in your own emotional response.""",
            5: """Make two columns on a piece of paper. On the left, write every myth about boundaries you've ever believed or been told: "Boundaries are selfish." "Good Christians don't set limits." "If I say no, they won't love me." "It's my job to keep everyone happy."

On the right, write the truth that counters each myth: "Boundaries are essential for real love." "Jesus set boundaries constantly." "People who can't handle my no were only using my yes." "I'm responsible for my actions, not others' feelings."

Post this somewhere you'll see it daily—bathroom mirror, refrigerator, car dashboard. Every day, read through it. Speak it out loud. Repetition is how we rewire belief systems.""",
            6: """The self-esteem inventory in McBride's work helps you assess where you are right now. Take it honestly—not how you wish you felt, but how you actually feel.

Then, write a letter to yourself using the following prompt: "Dear [Your Name], I know you've been struggling with [specific boundary challenge]. I want you to know that [words of compassion and understanding]..."

Write as if you were writing to a beloved friend who came to you with these struggles. Notice the difference between how you speak to a friend and how you typically speak to yourself.

Keep this letter. Read it when you're struggling. Update it as you grow.""",
            7: """Create three relationship maps—one for romantic relationships (past and present), one for friendships, and one for family relationships.

In each map, identify the role you typically play. Are you the caretaker? The fixer? The peacekeeper? The invisible one? The hero? The rebel?

Now look across all three maps. Are there patterns? Do you play the same role regardless of context? Or do you shift roles depending on the relationship type?

This awareness is powerful because roles tend to come with specific boundary challenges. Caretakers often have porous boundaries. Rebels often have overly rigid ones. Know your role, know your challenge.""",
            8: """Family gatherings are boundary minefields. Preparation is key.

Before your next family interaction, identify: Which family member is most likely to push my boundaries? What topic is most triggering? What situation is hardest for me?

Then prepare specific responses. Not vague ideas—specific words: "I'm not comfortable discussing that." "I need to step outside for a moment." "That's not something I'm willing to do."

Also prepare your exit strategy. Know how you'll leave if things get overwhelming. Having an escape plan reduces anxiety and increases your ability to stay present.

Finally, arrange a debrief partner—someone you can call or text afterward to process how it went.""",
            9: """This week, track your work or ministry hours honestly. Every meeting, every email, every text, every "quick question"—log it.

At the end of the week, total it up. Compare to what's sustainable. If you're over, where is the extra time going?

Then make a list of every time this week you said yes when you wanted to say no. For each one, ask: What was I afraid would happen if I said no? Is that fear realistic?

Choose one boundary to implement immediately. Start with something achievable. Send the email that says "I'll no longer be available after 6pm for non-emergencies." Make it specific, clear, and observable.""",
            10: """Grief isn't just for death. We grieve the childhood we didn't have, the relationship that wasn't healthy, the years spent with poor boundaries.

Create a grief ritual that works for you. Some ideas:
- Write a letter to your younger self acknowledging what they went through
- Create art that represents your losses
- Visit a meaningful place and spend time in silence
- Light a candle and speak your losses out loud
- Plant something as a symbol of what you're releasing and what you're growing

Schedule this ritual. Put it on your calendar. Give yourself at least an hour. Have tissues nearby. Let yourself feel whatever comes up.""",
            11: """Build a resilience toolkit with three components: internal resources, external supports, and early warning systems.

Internal resources: List five healthy coping strategies that work for you—exercise, journaling, prayer, breathing exercises, creative expression, time in nature. These are your go-to strategies when stress increases.

External supports: Identify three people you can call when you're struggling. Have actual conversations with them: "I'm working on my boundaries. Can I check in with you when it's hard?"

Early warning systems: Know your personal signs that you're slipping. For some it's insomnia. For others it's irritability. For others it's people-pleasing behaviors returning. Know your signs and watch for them.""",
            12: """A personal boundaries manifesto is a declaration of who you are and how you'll operate going forward. This isn't vague—it's specific.

Include:
- I believe... (your core beliefs about boundaries)
- I commit to... (specific behaviors you'll maintain)
- I will no longer... (specific behaviors you're stopping)
- I will ask for help when... (specific triggers for seeking support)
- I forgive myself when... (permission for imperfection)

Date it. Sign it. Post it where you'll see it. Consider sharing it with someone who can hold you accountable.""",
            13: """This week, do a scripture study on boundaries. Look for:
- Times Jesus said no
- Times Jesus withdrew to rest or pray
- Times God set limits or allowed consequences
- Times prophets drew boundaries with kings or people
- Proverbs or wisdom literature about limits

You might be surprised how much biblical support there is for boundaries. God respecting human free will is itself a boundary—God's refusal to force relationship.

Journal about how these examples speak to your current boundary challenges. How does faith support your boundary practice? How might you have misused faith to avoid boundaries?""",
            14: """Time for a digital audit. For one week, track:
- Total screen time per day
- Time on each app/platform
- How you feel before and after using each platform
- Times you reached for your phone without intention

At the end of the week, analyze the data. Which platforms drain you? Which add value? Where is mindless scrolling stealing time?

Then implement one boundary. Maybe it's: no screens in the bedroom. No social media before 9am. No email after 6pm. App time limits. Phone-free meals.

Commit to this boundary for two weeks. Track how it affects your mood, productivity, and presence.""",
            15: """Create your ongoing practice plan with daily, weekly, and monthly components.

Daily: What brief practice will you do every day? A morning intention? An evening reflection? A boundary check-in?

Weekly: What weekly practice will reinforce your learning? Journaling? Meeting with an accountability partner? Reviewing your manifesto?

Monthly: What monthly practice will help you assess your progress? A boundary audit? A self-assessment? A check-in with a therapist or counselor?

Write this plan down. Share it with someone who can ask you about it. Schedule it in your calendar. The practices you schedule are the practices you keep.""",
        }

        return f"""[SEGMENT 4: PRACTICAL APPLICATION - 4 minutes]

[VOICE: {VOICES['host']['name']}]

Alright, let's get practical. This week's exercise is specifically designed to help you apply what we've discussed. Elena, walk us through it.

[VOICE: {VOICES['counselor']['name']}]

{exercises.get(week, "This week, identify one area where you want to strengthen your boundaries and take one small action toward that goal.")}

{exercise_details.get(week, "")}

[VOICE: {VOICES['expert']['name']}]

I'd add one thing: don't try to change everything at once. The temptation when you're learning this material is to revolutionize your entire life by next Tuesday. That leads to burnout and discouragement.

Instead, pick one area. Start small. Success builds on success. Make one change, solidify it, then add another. This is a marathon, not a sprint.

[VOICE: {VOICES['host']['name']}]

That's such wise counsel. Progress over perfection. Consistency over intensity. Small steps in the right direction are still steps.

Here are three additional practices for this week:

**Daily Practice**: Take two minutes each morning to set an intention around boundaries. Before your feet hit the floor, ask yourself: What's one boundary I'll honor today? What's one situation where I need to be alert? This primes your brain to notice opportunities.

**Mid-week Check-in**: Wednesday, take five minutes to assess. How are you doing with the main exercise? What's working? What's hard? What adjustments do you need? Course-correct if necessary—that's not failure, it's wisdom.

**Weekend Reflection**: Before the week ends, journal about your experiences. What did you learn? What surprised you? What will you carry forward? Celebrate any progress, no matter how small. Celebration reinforces behavior.

[VOICE: {VOICES['counselor']['name']}]

And remember, setbacks are data, not disasters. If you struggle this week—and some of you will—get curious instead of critical. What triggered the struggle? What need were you trying to meet? What might you do differently next time?

Curiosity is more useful than criticism. Always.

[VOICE: {VOICES['expert']['name']}]

In faith language, there's grace for the journey. You're not expected to be perfect—you're invited to be present. God doesn't require flawless execution. God invites faithful engagement.
"""

    def _generate_reflection_section(self, week: int, week_data: Dict) -> str:
        """Generate reflection questions segment."""

        # Week-specific deep questions
        deep_questions = {
            1: [
                "Where in your life do you feel most 'invaded' by others?",
                "What would your life look like with healthy boundaries in place?",
                "What fears come up when you think about setting clearer limits?",
                "Who in your life models healthy boundaries? What can you learn from them?",
            ],
            2: [
                "What boundary patterns did you observe in your family growing up?",
                "At what age did you first learn that your needs were 'too much'?",
                "How has your attachment style affected your boundary setting?",
                "What developmental milestone might you need to revisit emotionally?",
            ],
            3: [
                "Which boundary problem type resonates most with you: Compliant, Avoidant, Controller, or Nonresponsive?",
                "What situations trigger your boundary problems most reliably?",
                "When did you last say yes when you meant no? What was the cost?",
                "How do you respond when others set boundaries with you?",
            ],
            4: [
                "In what relationship are you shielding someone from natural consequences?",
                "What are you taking responsibility for that isn't actually yours?",
                "Where are you trying to change something outside your power?",
                "Whose boundaries do you struggle to respect most?",
            ],
            5: [
                "What boundary myth has had the most power over you?",
                "Who taught you that boundaries are selfish? What was their motivation?",
                "Which type of boundary—physical, emotional, time, or energy—needs the most attention?",
                "How would your life change if you truly believed boundaries were healthy?",
            ],
            6: [
                "On a scale of 1-10, how would you rate your self-worth? What would move it up one point?",
                "How do your feelings about yourself affect the boundaries you set?",
                "What relationship has most impacted your self-esteem?",
                "If you truly loved yourself, what boundary would you set immediately?",
            ],
            7: [
                "What patterns from your family of origin show up in your adult relationships?",
                "How do your boundary issues manifest differently in romantic vs. friendship contexts?",
                "What cycle are you committed to breaking?",
                "Who might you need to have a boundary conversation with this week?",
            ],
            8: [
                "What family event or interaction typically challenges your boundaries most?",
                "How do you reconcile honoring parents with setting limits?",
                "What financial boundaries might you need with family members?",
                "If you had no fear of disappointing family, what would you do differently?",
            ],
            9: [
                "How many hours did you work last week? Is that sustainable?",
                "What's one thing you do at work that isn't really your responsibility?",
                "How do you handle boundary-pushing from those you serve?",
                "What would sustainable ministry/work look like for you?",
            ],
            10: [
                "What loss related to boundaries do you need to grieve?",
                "What childhood experience taught you boundaries were unsafe?",
                "Who can support you in your healing journey?",
                "What would grieving well look like for you?",
            ],
            11: [
                "What triggers tend to collapse your boundary progress?",
                "What does resilience look like in your specific context?",
                "How will you handle setbacks when they come?",
                "What new pattern are you most committed to establishing?",
            ],
            12: [
                "Where do you struggle most with self-discipline?",
                "How do your internal boundaries affect your external ones?",
                "What promise to yourself have you been breaking?",
                "What would integration look like in your daily life?",
            ],
            13: [
                "How has your faith helped or hindered your boundary work?",
                "Where do you see God modeling boundaries in Scripture?",
                "What would trusting God with your boundaries look like?",
                "How might healthy boundaries actually deepen your spiritual life?",
            ],
            14: [
                "How many hours a day are you on screens? How does that feel?",
                "What social media platform most drains you?",
                "What would healthy technology use look like for you?",
                "What's one digital boundary you're willing to implement this week?",
            ],
            15: [
                "What's the most significant thing you've learned in this course?",
                "How has your understanding of boundaries changed?",
                "What boundary practice will you maintain going forward?",
                "Who will you share your learning with?",
            ],
        }

        questions = deep_questions.get(
            week,
            [
                "What stood out to you most from this week's content?",
                "Where do you see room for growth?",
                "What's one small step you can take this week?",
                "Who can support you in this work?",
            ],
        )

        return f"""[SEGMENT 5: REFLECTION QUESTIONS - 2 minutes]

[VOICE: {VOICES['host']['name']}]

Before we close, I want to leave you with some reflection questions. You might want to pause the podcast here and journal, or simply let these questions sit with you through the week.

This week's reflection focus is: {week_data['reflection_focus']}

Here are four questions to ponder:

**Question One**: {questions[0]}

Take a breath. Don't rush to answer. Let the question do its work.

**Question Two**: {questions[1]}

Again, no need to have a neat answer. The questions are invitations, not tests.

**Question Three**: {questions[2]}

Notice what comes up. Resistance? Curiosity? Relief?

**Question Four**: {questions[3]}

Consider journaling about these questions this week.

[VOICE: {VOICES['counselor']['name']}]

Remember, reflection isn't meant to be comfortable. Good questions should challenge us. If these questions stir something up, that's information worth attending to.

[VOICE: {VOICES['expert']['name']}]

And hold these questions with grace. You're doing important work. The fact that you're engaging at all is significant.
"""

    def _generate_closing(self, week: int, week_data: Dict) -> str:
        """Generate closing segment."""

        next_week = COURSE_STRUCTURE.get(week + 1, {})
        next_week_preview = ""

        if next_week:
            next_week_preview = f"""Next week, we'll explore {next_week.get('title', 'new concepts')}, covering {', '.join(next_week.get('readings', ['additional readings']))}. This builds directly on what we've discussed today.

**Your preparation for Week {week + 1}:**

Complete the readings: {', '.join(next_week.get('readings', ['See syllabus']))}. If you can only read one thing, prioritize the first reading listed. But if you can engage with all of them, you'll get so much more from our discussion.

Continue this week's practical exercise. The exercises are designed to compound—each week's work prepares you for the next.

Notice what themes from this week show up in your daily life. Awareness is your homework. When you see {week_data['themes'][0].lower()} in action, note it. When you catch yourself in old patterns, note it. When you successfully hold a boundary, note it and celebrate.

Consider discussing this week's content with someone you trust. Shared learning deepens learning. And you might find that others are struggling with similar issues."""
        else:
            next_week_preview = """We've reached the end of our 15-week journey together. Let me take a moment to acknowledge what you've done.

You've shown up, week after week. You've engaged with challenging material. You've looked at yourself honestly—at your patterns, your pain, your potential. That takes courage.

This isn't an ending—it's a beginning. The real work of boundary-keeping happens in the moments and days and years ahead. The course gave you knowledge. Your life will give you practice.

Here's what I want you to remember:

**You have tools now.** You understand what boundaries are, how they develop, what goes wrong, and how to heal. You have language for your experience. You have frameworks for understanding.

**You have community.** Everyone who's taken this course is on a similar journey. You're not alone in this work. Seek out others who understand.

**You have permission.** Permission to take care of yourself. Permission to say no. Permission to have needs. Permission to be a whole person. If you needed someone to give you permission, consider it given.

**Change is possible.** Neuroplasticity is real. New patterns can be established at any age. The path you've been on isn't the only path available.

Stay connected. Keep practicing. Trust the process. And remember: boundaries aren't barriers to love—they're the architecture of healthy relationship.

[VOICE: {VOICES['counselor']['name']}]

From a clinical perspective, I want to add: the growth you've done in this course may need reinforcement. Consider finding a therapist or counselor who can support your ongoing work. Consider joining a group focused on healthy relating. The insights from these weeks are seeds—they need ongoing watering.

[VOICE: {VOICES['expert']['name']}]

From a ministry perspective: you're now equipped to lead differently. The boundaries you establish personally create possibilities for those you serve. Healthy leaders create healthy communities. Your personal work has collective impact.

May you go with grace, clarity, and the courage to hold the limits that allow love to flourish."""

        # Week-specific closing encouragements
        closing_encouragements = {
            1: "You've taken the first step into a new way of understanding yourself. That first step is often the hardest. Be proud of yourself for beginning.",
            2: "Understanding your history is powerful. It's not about blame—it's about freedom. When you know where patterns came from, you gain the power to change them.",
            3: "Seeing your boundary problems clearly is uncomfortable but essential. You can't fix what you won't face. You've faced it this week.",
            4: "The laws of boundaries aren't restrictions—they're liberations. Working with reality instead of against it is the path to sustainable change.",
            5: "Every myth you release is space for truth. You're making room for a new story about what boundaries mean and who you're allowed to be.",
            6: "The connection between self and boundaries is profound. As you grow in self-worth, your boundaries strengthen. As your boundaries strengthen, your self-worth grows. It's a virtuous cycle.",
            7: "Changing relationship patterns is some of the hardest work we do. But it's also some of the most rewarding. Keep going.",
            8: "Family work is heart work. The courage to set boundaries with those you love most is extraordinary courage. Honor that in yourself.",
            9: "Sustainable ministry requires sustainable ministers. Taking care of yourself isn't selfish—it's strategic. You're playing the long game now.",
            10: "Grief work is holy work. What you're mourning deserves to be mourned. Let yourself feel it. On the other side is freedom.",
            11: "Recovery isn't a destination—it's a direction. You're pointed the right way. Keep walking, even when progress feels slow.",
            12: "Integration takes time. Be patient with yourself as you put the pieces together. The goal isn't perfection—it's practice.",
            13: "Faith and boundaries can coexist. In fact, they strengthen each other. Your spiritual life supports your boundary life, and vice versa.",
            14: "Digital boundaries are essential in our age. Your attention is valuable—guard it. Your presence is a gift—protect it.",
            15: "You've completed something significant. Carry what you've learned into every relationship, every day, every moment. You're equipped for a new way of living.",
        }

        return f"""[SEGMENT 6: CLOSING - 3 minutes]

[VOICE: {VOICES['host']['name']}]

As we wrap up Week {week}, I want to leave you with some encouragement.

{closing_encouragements.get(week, "You're doing important work. Keep going.")}

{next_week_preview}

[VOICE: {VOICES['expert']['name']}]

This has been a rich conversation. I'm grateful for each listener engaging with this material. The work you're doing matters—not just for you, but for everyone your life touches. When leaders become healthier, organizations become healthier. When individuals learn boundaries, families transform.

You're not just doing this for yourself. You're doing it for everyone who will benefit from the more boundaried, more present, more whole version of you. That's a lot of people.

[VOICE: {VOICES['counselor']['name']}]

Remember, change takes time. Neural pathways don't rewire overnight. Be patient with yourself. Celebrate progress. Seek support when you need it. 

If you're finding this material brings up a lot for you—old memories, strong emotions, difficult realizations—that's normal. It means the work is working. But it also means you might benefit from additional support. Consider reaching out to a therapist or counselor who can walk alongside you.

You're not meant to do this alone. None of us are.

[VOICE: {VOICES['host']['name']}]

Thank you for joining us for Week {week} of Healthy Boundaries for Leaders. I'm {VOICES['host']['name']}, alongside {VOICES['expert']['name']} and {VOICES['counselor']['name']}.

Before you go, remember our three takeaways from today:

**First**: {week_data['key_concepts'][0].title()} is essential for understanding {week_data['title'].lower()}.

**Second**: This week's practical exercise—do it. Don't just think about it, do it. Application is where transformation happens.

**Third**: Be compassionate with yourself in this work. Growth is rarely linear. Honor your pace.

Until next time, remember: Boundaries aren't barriers to love—they're the architecture of healthy relationship. They're not walls that keep people out—they're doors that let the right things in.

Take care of yourselves, friends. And take care of each other.

[MUSIC: Theme music fades in]

[END OF EPISODE]

{'='*70}
EPISODE {week} COMPLETE
Word Count: ~3000 words
Duration: ~20 minutes
{'='*70}
"""

    def save_script(self, week: int, script: str):
        """Save the script to a file."""
        filename = f"week_{week:02d}_podcast_script.txt"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(script)

        word_count = len(script.split())
        print(f"  ✓ Saved: {filename} ({word_count} words)")


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def main():
    """Main entry point."""
    output_dir = (
        PROJECT_ROOT
        / "content"
        / "courses"
        / "HB411_HealthyBoundaries"
        / "podcast_scripts"
    )

    generator = PodcastScriptGenerator(output_dir)
    generator.generate_all_scripts()

    # Print summary
    print("\n📊 Generation Summary:")
    print(f"   Output directory: {output_dir}")
    print(f"   Scripts generated: 15")
    print(f"   Target duration: ~20 minutes each")
    print(f"   Target word count: ~3000 words each")
    print("\n💡 Next steps:")
    print("   1. Review generated scripts for accuracy")
    print("   2. Customize voice annotations as needed")
    print("   3. Use for TTS generation or live recording")
    print("   4. Consider adding course-specific examples")


if __name__ == "__main__":
    main()
