"""
Content Workflow for OsMEN

Content generation workflow for blogs, social media, and marketing content.
Supports multiple content types with quality benchmarking.

Usage:
    from workflows.content import ContentWorkflow
    
    workflow = ContentWorkflow()
    
    # Generate blog post
    result = await workflow.generate_blog(
        topic="AI Agent Frameworks",
        tone="professional",
        length="medium"
    )
    
    # Generate social media content
    result = await workflow.generate_social(
        topic="Product Launch",
        platforms=["twitter", "linkedin"]
    )
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Types of content"""
    BLOG_POST = "blog_post"
    SOCIAL_TWITTER = "social_twitter"
    SOCIAL_LINKEDIN = "social_linkedin"
    SOCIAL_INSTAGRAM = "social_instagram"
    EMAIL_NEWSLETTER = "email_newsletter"
    PRODUCT_DESCRIPTION = "product_description"
    PRESS_RELEASE = "press_release"
    FAQ = "faq"


class ContentTone(str, Enum):
    """Tone options for content"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    HUMOROUS = "humorous"
    INSPIRING = "inspiring"
    EDUCATIONAL = "educational"


class ContentLength(str, Enum):
    """Content length options"""
    SHORT = "short"    # ~200 words / 1-2 paragraphs
    MEDIUM = "medium"  # ~500 words / 3-5 paragraphs
    LONG = "long"      # ~1000+ words / 5+ paragraphs


@dataclass
class ContentSection:
    """A section of content"""
    heading: Optional[str]
    content: str
    word_count: int = 0
    
    def __post_init__(self):
        self.word_count = len(self.content.split())


@dataclass
class ContentResult:
    """Generated content result"""
    id: str
    content_type: ContentType
    title: str
    sections: List[ContentSection]
    metadata: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def full_content(self) -> str:
        """Get full content as string"""
        parts = []
        for section in self.sections:
            if section.heading:
                parts.append(f"## {section.heading}\n")
            parts.append(section.content)
            parts.append("")
        return "\n".join(parts)
    
    @property
    def word_count(self) -> int:
        """Total word count"""
        return sum(s.word_count for s in self.sections)
    
    def to_markdown(self) -> str:
        """Convert to markdown"""
        lines = [f"# {self.title}", ""]
        
        for section in self.sections:
            if section.heading:
                lines.append(f"## {section.heading}")
                lines.append("")
            lines.append(section.content)
            lines.append("")
        
        lines.extend([
            "---",
            f"*Generated: {self.created_at.strftime('%Y-%m-%d %H:%M')}*",
            f"*Word count: {self.word_count}*"
        ])
        
        return "\n".join(lines)
    
    def to_html(self) -> str:
        """Convert to HTML"""
        sections_html = []
        for section in self.sections:
            if section.heading:
                sections_html.append(f"<h2>{section.heading}</h2>")
            # Convert paragraphs
            paragraphs = section.content.split("\n\n")
            for p in paragraphs:
                if p.strip():
                    sections_html.append(f"<p>{p.strip()}</p>")
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{self.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; margin-top: 30px; }}
        p {{ line-height: 1.6; color: #444; }}
    </style>
</head>
<body>
    <h1>{self.title}</h1>
    {''.join(sections_html)}
</body>
</html>"""


@dataclass
class SocialPost:
    """Social media post"""
    platform: str
    content: str
    hashtags: List[str]
    character_count: int = 0
    
    def __post_init__(self):
        self.character_count = len(self.content)
    
    @property
    def with_hashtags(self) -> str:
        """Content with hashtags appended"""
        tags = " ".join(f"#{tag}" for tag in self.hashtags)
        return f"{self.content}\n\n{tags}"


class ContentGenerator:
    """
    Generates various types of content.
    
    Uses templates and LLM for content generation.
    """
    
    def __init__(self, llm_provider=None):
        """
        Initialize content generator.
        
        Args:
            llm_provider: LLM provider for generation
        """
        self.llm = llm_provider
        
        # Content templates
        self._templates = {
            ContentType.BLOG_POST: self._generate_blog_template,
            ContentType.SOCIAL_TWITTER: self._generate_twitter_template,
            ContentType.SOCIAL_LINKEDIN: self._generate_linkedin_template,
            ContentType.EMAIL_NEWSLETTER: self._generate_newsletter_template,
            ContentType.PRODUCT_DESCRIPTION: self._generate_product_template,
        }
    
    async def generate(
        self,
        content_type: ContentType,
        topic: str,
        tone: ContentTone = ContentTone.PROFESSIONAL,
        length: ContentLength = ContentLength.MEDIUM,
        keywords: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ContentResult:
        """
        Generate content.
        
        Args:
            content_type: Type of content to generate
            topic: Topic/subject of content
            tone: Tone of content
            length: Length of content
            keywords: Optional keywords to include
            context: Additional context
            
        Returns:
            Generated content result
        """
        generator = self._templates.get(content_type)
        if not generator:
            raise ValueError(f"Unsupported content type: {content_type}")
        
        return await generator(topic, tone, length, keywords, context)
    
    async def _generate_blog_template(
        self,
        topic: str,
        tone: ContentTone,
        length: ContentLength,
        keywords: Optional[List[str]],
        context: Optional[Dict[str, Any]]
    ) -> ContentResult:
        """Generate blog post content"""
        
        # Determine section count based on length
        section_count = {
            ContentLength.SHORT: 2,
            ContentLength.MEDIUM: 4,
            ContentLength.LONG: 6
        }[length]
        
        # Generate title
        title = self._generate_title(topic, tone)
        
        # Generate sections
        sections = []
        
        # Introduction
        sections.append(ContentSection(
            heading=None,
            content=self._generate_intro(topic, tone)
        ))
        
        # Body sections
        section_topics = self._generate_section_topics(topic, section_count - 2)
        for section_topic in section_topics:
            sections.append(ContentSection(
                heading=section_topic,
                content=self._generate_section_content(section_topic, tone, length)
            ))
        
        # Conclusion
        sections.append(ContentSection(
            heading="Conclusion",
            content=self._generate_conclusion(topic, tone)
        ))
        
        return ContentResult(
            id=str(uuid4()),
            content_type=ContentType.BLOG_POST,
            title=title,
            sections=sections,
            metadata={
                "tone": tone.value,
                "length": length.value,
                "keywords": keywords or [],
                "topic": topic
            }
        )
    
    async def _generate_twitter_template(
        self,
        topic: str,
        tone: ContentTone,
        length: ContentLength,
        keywords: Optional[List[str]],
        context: Optional[Dict[str, Any]]
    ) -> ContentResult:
        """Generate Twitter/X thread"""
        
        # Generate thread
        thread = self._generate_twitter_thread(topic, tone)
        
        sections = [
            ContentSection(
                heading=f"Tweet {i+1}",
                content=tweet
            )
            for i, tweet in enumerate(thread)
        ]
        
        return ContentResult(
            id=str(uuid4()),
            content_type=ContentType.SOCIAL_TWITTER,
            title=f"Twitter Thread: {topic}",
            sections=sections,
            metadata={
                "tone": tone.value,
                "platform": "twitter",
                "tweet_count": len(thread),
                "topic": topic
            }
        )
    
    async def _generate_linkedin_template(
        self,
        topic: str,
        tone: ContentTone,
        length: ContentLength,
        keywords: Optional[List[str]],
        context: Optional[Dict[str, Any]]
    ) -> ContentResult:
        """Generate LinkedIn post"""
        
        content = self._generate_linkedin_post(topic, tone)
        
        sections = [
            ContentSection(heading=None, content=content)
        ]
        
        return ContentResult(
            id=str(uuid4()),
            content_type=ContentType.SOCIAL_LINKEDIN,
            title=f"LinkedIn Post: {topic}",
            sections=sections,
            metadata={
                "tone": tone.value,
                "platform": "linkedin",
                "topic": topic
            }
        )
    
    async def _generate_newsletter_template(
        self,
        topic: str,
        tone: ContentTone,
        length: ContentLength,
        keywords: Optional[List[str]],
        context: Optional[Dict[str, Any]]
    ) -> ContentResult:
        """Generate email newsletter"""
        
        sections = [
            ContentSection(
                heading="Hello!",
                content=f"Welcome to this week's newsletter where we dive into {topic}."
            ),
            ContentSection(
                heading="The Big Picture",
                content=self._generate_section_content(topic, tone, ContentLength.MEDIUM)
            ),
            ContentSection(
                heading="Key Takeaways",
                content=self._generate_takeaways(topic)
            ),
            ContentSection(
                heading="What's Next",
                content="Stay tuned for more insights in our next edition. Don't forget to share with colleagues who might find this valuable!"
            )
        ]
        
        return ContentResult(
            id=str(uuid4()),
            content_type=ContentType.EMAIL_NEWSLETTER,
            title=f"Newsletter: {topic}",
            sections=sections,
            metadata={
                "tone": tone.value,
                "topic": topic
            }
        )
    
    async def _generate_product_template(
        self,
        topic: str,
        tone: ContentTone,
        length: ContentLength,
        keywords: Optional[List[str]],
        context: Optional[Dict[str, Any]]
    ) -> ContentResult:
        """Generate product description"""
        
        sections = [
            ContentSection(
                heading=None,
                content=self._generate_product_intro(topic, tone)
            ),
            ContentSection(
                heading="Key Features",
                content=self._generate_features_list(topic)
            ),
            ContentSection(
                heading="Benefits",
                content=self._generate_benefits(topic)
            ),
            ContentSection(
                heading="Get Started",
                content=f"Ready to experience {topic}? Start your journey today and see the difference it makes."
            )
        ]
        
        return ContentResult(
            id=str(uuid4()),
            content_type=ContentType.PRODUCT_DESCRIPTION,
            title=topic,
            sections=sections,
            metadata={
                "tone": tone.value,
                "topic": topic
            }
        )
    
    def _generate_title(self, topic: str, tone: ContentTone) -> str:
        """Generate a title for the content"""
        titles = {
            ContentTone.PROFESSIONAL: f"A Comprehensive Guide to {topic}",
            ContentTone.CASUAL: f"Everything You Need to Know About {topic}",
            ContentTone.FRIENDLY: f"Let's Talk About {topic}!",
            ContentTone.FORMAL: f"An Analysis of {topic}",
            ContentTone.HUMOROUS: f"The Wild World of {topic}",
            ContentTone.INSPIRING: f"Unlock the Power of {topic}",
            ContentTone.EDUCATIONAL: f"Understanding {topic}: A Deep Dive"
        }
        return titles.get(tone, f"About {topic}")
    
    def _generate_intro(self, topic: str, tone: ContentTone) -> str:
        """Generate introduction paragraph"""
        intros = {
            ContentTone.PROFESSIONAL: f"In today's rapidly evolving landscape, understanding {topic} has become essential for professionals and organizations alike. This comprehensive guide explores the key concepts, best practices, and practical applications that will help you master this important subject.",
            ContentTone.CASUAL: f"Hey there! So you want to learn about {topic}? You've come to the right place. Let's break it down in a way that actually makes sense.",
            ContentTone.FRIENDLY: f"Welcome! We're excited to share our insights on {topic} with you. Whether you're just starting out or looking to deepen your knowledge, we've got you covered.",
            ContentTone.EDUCATIONAL: f"{topic} represents a significant area of study with far-reaching implications. This article aims to provide a thorough examination of the subject, covering fundamental concepts through advanced applications."
        }
        return intros.get(tone, f"This article explores {topic} in detail, providing valuable insights and practical guidance.")
    
    def _generate_section_topics(self, topic: str, count: int) -> List[str]:
        """Generate section topics for a blog post"""
        base_topics = [
            f"What is {topic}?",
            f"Key Components of {topic}",
            f"Benefits of {topic}",
            f"Getting Started with {topic}",
            f"Best Practices for {topic}",
            f"Common Challenges in {topic}",
            f"Future of {topic}",
            f"Real-World Applications"
        ]
        return base_topics[:count]
    
    def _generate_section_content(
        self,
        section_topic: str,
        tone: ContentTone,
        length: ContentLength
    ) -> str:
        """Generate content for a section"""
        word_targets = {
            ContentLength.SHORT: 50,
            ContentLength.MEDIUM: 100,
            ContentLength.LONG: 200
        }
        
        # Generate placeholder content based on tone
        content = f"""When examining {section_topic}, several important factors come into play. Understanding these elements is crucial for anyone looking to gain expertise in this area.

First, it's important to recognize the foundational concepts that underpin {section_topic}. These basics provide the framework for more advanced understanding and practical application.

Furthermore, real-world experience shows that success in this area often comes from consistent practice and continuous learning. The most effective practitioners combine theoretical knowledge with hands-on experimentation."""
        
        return content
    
    def _generate_conclusion(self, topic: str, tone: ContentTone) -> str:
        """Generate conclusion paragraph"""
        return f"""As we've explored throughout this article, {topic} offers significant opportunities for those willing to invest the time and effort to understand it deeply. By applying the principles and practices discussed here, you'll be well-positioned to achieve meaningful results.

Remember that mastery is a journey, not a destination. Continue learning, experimenting, and refining your approach. The insights you gain along the way will prove invaluable.

We hope this guide has provided you with actionable knowledge and inspiration to take your next steps with confidence."""
    
    def _generate_twitter_thread(
        self,
        topic: str,
        tone: ContentTone
    ) -> List[str]:
        """Generate a Twitter thread"""
        return [
            f"🧵 Thread: A quick guide to {topic}! Let's dive in 👇",
            f"1/ First, let's understand the basics. {topic} is transforming how we work and think about solutions.",
            f"2/ The key insight? Focus on fundamentals. Master the basics before moving to advanced techniques.",
            f"3/ Common mistake to avoid: Trying to do everything at once. Start small, iterate, and scale.",
            f"4/ Pro tip: Document your journey. What you learn helps others (and future you!).",
            f"5/ Ready to start? Begin with these three steps:\n\n• Learn the core concepts\n• Practice daily\n• Join the community",
            f"6/ That's a wrap! Follow for more insights on {topic}. RT if you found this helpful! 🙏"
        ]
    
    def _generate_linkedin_post(self, topic: str, tone: ContentTone) -> str:
        """Generate a LinkedIn post"""
        return f"""I've been thinking a lot about {topic} lately, and I wanted to share some insights. 🎯

Over the past few months, I've noticed a significant shift in how professionals approach this area. Here's what stands out:

📌 The fundamentals matter more than ever
📌 Community learning accelerates growth
📌 Practical application beats theory every time

The most successful people I've worked with share one trait: they're not afraid to experiment and learn from failures.

My advice? Start small, stay consistent, and don't be afraid to share your journey.

What's your experience with {topic}? I'd love to hear your thoughts in the comments.

#ProfessionalDevelopment #Learning #Growth"""
    
    def _generate_takeaways(self, topic: str) -> str:
        """Generate key takeaways"""
        return f"""• Understanding {topic} starts with mastering the fundamentals
• Practical experience is invaluable - learn by doing
• Stay current with industry trends and best practices
• Connect with others who share your interests
• Continuous improvement leads to lasting success"""
    
    def _generate_product_intro(self, topic: str, tone: ContentTone) -> str:
        """Generate product introduction"""
        return f"""Introducing {topic} - the solution you've been waiting for. Designed with your needs in mind, this product delivers exceptional results while saving you time and effort. Whether you're a beginner or an expert, you'll find exactly what you need to succeed."""
    
    def _generate_features_list(self, topic: str) -> str:
        """Generate features list"""
        return f"""• **Easy to Use**: Intuitive design means you can get started immediately
• **Powerful Performance**: Advanced capabilities that grow with your needs  
• **Seamless Integration**: Works with your existing tools and workflows
• **Reliable Support**: Expert assistance whenever you need it
• **Continuous Updates**: Always improving based on user feedback"""
    
    def _generate_benefits(self, topic: str) -> str:
        """Generate benefits"""
        return f"""By choosing {topic}, you'll experience:

- **Increased Productivity**: Accomplish more in less time
- **Better Results**: Achieve outcomes that exceed expectations
- **Peace of Mind**: Reliable performance you can count on
- **Competitive Edge**: Stay ahead with cutting-edge capabilities"""


class ContentWorkflow:
    """
    Complete content generation workflow.
    
    Supports multiple content types with quality benchmarking.
    """
    
    def __init__(self, llm_provider=None):
        """
        Initialize content workflow.
        
        Args:
            llm_provider: LLM provider for generation
        """
        self.llm = llm_provider
        self.generator = ContentGenerator(llm_provider)
    
    async def generate_blog(
        self,
        topic: str,
        tone: str = "professional",
        length: str = "medium",
        keywords: Optional[List[str]] = None,
        outline: Optional[List[str]] = None
    ) -> ContentResult:
        """
        Generate a blog post.
        
        Args:
            topic: Blog topic
            tone: Content tone
            length: Content length
            keywords: SEO keywords
            outline: Optional section outline
            
        Returns:
            Generated blog content
        """
        logger.info(f"Generating blog post on: {topic}")
        
        return await self.generator.generate(
            content_type=ContentType.BLOG_POST,
            topic=topic,
            tone=ContentTone(tone),
            length=ContentLength(length),
            keywords=keywords,
            context={"outline": outline}
        )
    
    async def generate_social(
        self,
        topic: str,
        platforms: List[str] = None,
        tone: str = "friendly"
    ) -> Dict[str, ContentResult]:
        """
        Generate social media content for multiple platforms.
        
        Args:
            topic: Content topic
            platforms: Target platforms
            tone: Content tone
            
        Returns:
            Dictionary of platform -> content
        """
        platforms = platforms or ["twitter", "linkedin"]
        logger.info(f"Generating social content for: {platforms}")
        
        results = {}
        
        for platform in platforms:
            content_type = {
                "twitter": ContentType.SOCIAL_TWITTER,
                "linkedin": ContentType.SOCIAL_LINKEDIN,
                "instagram": ContentType.SOCIAL_INSTAGRAM
            }.get(platform)
            
            if content_type:
                result = await self.generator.generate(
                    content_type=content_type,
                    topic=topic,
                    tone=ContentTone(tone),
                    length=ContentLength.SHORT
                )
                results[platform] = result
        
        return results
    
    async def generate_newsletter(
        self,
        topic: str,
        tone: str = "friendly",
        include_cta: bool = True
    ) -> ContentResult:
        """
        Generate email newsletter.
        
        Args:
            topic: Newsletter topic
            tone: Content tone
            include_cta: Include call-to-action
            
        Returns:
            Generated newsletter
        """
        logger.info(f"Generating newsletter on: {topic}")
        
        return await self.generator.generate(
            content_type=ContentType.EMAIL_NEWSLETTER,
            topic=topic,
            tone=ContentTone(tone),
            length=ContentLength.MEDIUM,
            context={"include_cta": include_cta}
        )
    
    async def generate_product_description(
        self,
        product_name: str,
        features: Optional[List[str]] = None,
        tone: str = "professional"
    ) -> ContentResult:
        """
        Generate product description.
        
        Args:
            product_name: Product name
            features: Key features
            tone: Content tone
            
        Returns:
            Generated description
        """
        logger.info(f"Generating product description for: {product_name}")
        
        return await self.generator.generate(
            content_type=ContentType.PRODUCT_DESCRIPTION,
            topic=product_name,
            tone=ContentTone(tone),
            length=ContentLength.MEDIUM,
            context={"features": features}
        )
    
    async def generate_campaign(
        self,
        topic: str,
        content_types: List[str] = None,
        tone: str = "professional"
    ) -> Dict[str, ContentResult]:
        """
        Generate a complete content campaign.
        
        Args:
            topic: Campaign topic
            content_types: Types of content to generate
            tone: Content tone
            
        Returns:
            Dictionary of content type -> content
        """
        content_types = content_types or ["blog", "twitter", "linkedin", "newsletter"]
        logger.info(f"Generating campaign for: {topic}")
        
        results = {}
        
        for ct in content_types:
            if ct == "blog":
                results["blog"] = await self.generate_blog(topic, tone=tone)
            elif ct == "newsletter":
                results["newsletter"] = await self.generate_newsletter(topic, tone=tone)
            elif ct in ["twitter", "linkedin"]:
                social = await self.generate_social(topic, [ct], tone=tone)
                results[ct] = social.get(ct)
        
        return results


# CLI interface
async def main():
    """CLI entry point for content workflow"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OsMEN Content Workflow")
    parser.add_argument("topic", help="Content topic")
    parser.add_argument("--type", choices=["blog", "social", "newsletter", "campaign"], default="blog")
    parser.add_argument("--tone", choices=["professional", "casual", "friendly"], default="professional")
    parser.add_argument("--length", choices=["short", "medium", "long"], default="medium")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--format", choices=["markdown", "html"], default="markdown")
    
    args = parser.parse_args()
    
    workflow = ContentWorkflow()
    
    if args.type == "blog":
        result = await workflow.generate_blog(args.topic, tone=args.tone, length=args.length)
        output = result.to_html() if args.format == "html" else result.to_markdown()
    elif args.type == "social":
        results = await workflow.generate_social(args.topic, tone=args.tone)
        output = "\n\n---\n\n".join(r.to_markdown() for r in results.values())
    elif args.type == "newsletter":
        result = await workflow.generate_newsletter(args.topic, tone=args.tone)
        output = result.to_markdown()
    elif args.type == "campaign":
        results = await workflow.generate_campaign(args.topic, tone=args.tone)
        output = "\n\n---\n\n".join(r.to_markdown() for r in results.values() if r)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Content saved to: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    asyncio.run(main())
