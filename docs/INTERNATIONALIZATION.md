# Internationalization (i18n)

Current language support and internationalization policy for OsMEN.

## Current Status

**OsMEN is currently English-only.**

All user interfaces, documentation, and system messages are in English.

## Language Support Policy

### Why English Only?

We are focusing on core functionality and stability first. Internationalization will be considered for future releases based on:

1. **User Demand:** Clear need from non-English speaking users
2. **Community Support:** Contributors willing to maintain translations
3. **Resource Availability:** Development time for i18n infrastructure

### Future Plans

Internationalization is on our roadmap for **v3.0.0 (2025 Q3)**.

## If You Need Non-English Support

### Current Options

1. **Browser Translation**
   - Use built-in browser translation (Chrome, Edge, Firefox)
   - Quality may vary, especially for technical terms

2. **Screen Reader Translation**
   - Some screen readers offer translation features
   - May help with accessibility

3. **LLM Multilingual Support**
   - Many LLM providers support multiple languages
   - Agent responses can be in any language you prompt in
   - Example: "Respond in Spanish" or "Responde en español"

### Community Translations

If you'd like to contribute translations:

1. Star and watch the repository for updates
2. Comment on [Issue #i18n](https://github.com/dwilli15/OsMEN/issues) (to be created)
3. Express interest in your language
4. We'll notify you when i18n support begins

## Technical Details

### When i18n Support Comes

We plan to use:

- **Framework:** GNU gettext or i18next
- **File Format:** JSON or PO files
- **Supported Areas:**
  - Web UI strings
  - Error messages
  - System notifications
  - Documentation (gradually)

### What Will Be Translated

**High Priority:**
- [ ] Web dashboard UI
- [ ] Error messages
- [ ] System notifications
- [ ] Form labels and buttons
- [ ] Help text

**Medium Priority:**
- [ ] README.md and quick start guides
- [ ] API documentation
- [ ] Agent response templates

**Low Priority:**
- [ ] Comprehensive documentation
- [ ] Code comments
- [ ] Development guides

### What Will Remain English

Some content will stay in English:

- Code and variable names
- Configuration file keys
- Log messages (for debugging)
- API endpoints
- Database schema

## Planned Language Support (v3.0+)

### Priority Languages

Based on user base and demand, priority languages may include:

1. **Spanish** (es) - Large user base
2. **French** (fr) - European market
3. **German** (de) - European market
4. **Portuguese** (pt) - Brazilian market
5. **Chinese Simplified** (zh-CN) - Asian market
6. **Japanese** (ja) - Asian market

### Community Languages

Additional languages supported by community contributors:

- Italian (it)
- Dutch (nl)
- Russian (ru)
- Korean (ko)
- And others based on contributions

## Right-to-Left (RTL) Support

RTL languages (Arabic, Hebrew, etc.) require additional work:

- UI layout adjustments
- Text direction handling
- Mirror interface elements

**Status:** Not planned for initial i18n release (v3.0)  
**Future:** Will be considered for v3.1+ if there's demand

## Localization vs. Internationalization

### Internationalization (i18n)
Making the software capable of being translated.

**Our Responsibility:**
- Extract strings for translation
- Support multiple languages in code
- Handle date/time formats
- Support number formats

### Localization (l10n)
Actual translation to specific languages.

**Community Responsibility:**
- Translate strings
- Review translations
- Maintain translations
- Test in target language

## How to Contribute (When Available)

### Translation Process (Future)

1. **Join Translation Team**
   - Express interest on GitHub
   - Receive translator access

2. **Translate Strings**
   - Use translation platform (Crowdin/Weblate)
   - Follow translation guidelines
   - Maintain consistency

3. **Review and Test**
   - Peer review translations
   - Test in actual application
   - Report issues

### Translation Guidelines (Future)

- Maintain tone and voice
- Keep technical terms consistent
- Don't translate:
  - Product name "OsMEN"
  - Feature names (unless cultural adaptation needed)
  - Code-related terms
- Use appropriate formality level
- Consider cultural context

## Workarounds

### Using OsMEN in Non-English Environments

**LLM Language Support:**
```bash
# In .env, set your preferred language for agent responses
DEFAULT_AGENT_LANGUAGE=es  # Spanish
DEFAULT_AGENT_LANGUAGE=fr  # French
DEFAULT_AGENT_LANGUAGE=de  # German
```

**Custom Prompts:**
```python
# When calling agents, specify language
prompt = "Respond in German: What is the weather today?"
result = agent.execute(prompt)
```

**Documentation Translation:**
- Community members can translate docs
- Host on personal repos or wikis
- Link from main repo (we'll add a translations section)

## Roadmap

### v2.x (Current)
- ✅ English only
- ✅ Focus on core features
- ✅ Stable API

### v3.0 (2025 Q3)
- [ ] i18n infrastructure
- [ ] English + 2-3 major languages
- [ ] Translation platform setup
- [ ] Community translator program

### v3.1+ (2025 Q4+)
- [ ] Additional languages
- [ ] Community-contributed languages
- [ ] RTL support (if needed)
- [ ] Locale-specific features

## Questions?

- **General i18n Questions:** Open a [GitHub Discussion](https://github.com/dwilli15/OsMEN/discussions)
- **Translation Interest:** Comment on i18n tracking issue
- **Technical Questions:** Email: i18n@osmen.dev

## Resources

- [W3C Internationalization Best Practices](https://www.w3.org/International/)
- [Unicode CLDR](https://cldr.unicode.org/)
- [i18next Documentation](https://www.i18next.com/)
- [GNU gettext Manual](https://www.gnu.org/software/gettext/)

---

**Last Updated:** 2024-11-18  
**Current Status:** English Only  
**i18n Target:** v3.0.0 (2025 Q3)
