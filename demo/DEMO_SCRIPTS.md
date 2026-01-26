# 🎬 FinFind Demo Scripts

Complete walkthrough scripts for demonstrating FinFind's capabilities during the hackathon presentation.

---

## Pre-Demo Setup

### Environment Checklist
```bash
# 1. Ensure backend is running
curl http://localhost:8000/health

# 2. Ensure frontend is running
# Open http://localhost:3000

# 3. Load demo data
python demo/load_demo_data.py

# 4. Verify demo user exists
curl http://localhost:8000/users/demo_student_001/profile
```

### Browser Setup
- Open Chrome/Firefox in clean profile
- Disable extensions that might interfere
- Set zoom to 100%
- Open DevTools Network tab (minimized) for showing API calls
- Have backup demo video ready

---

## Scenario 1: Vague Intent Search with Budget Constraints

### Setup
- Login as: `demo_student_001` (Sarah Chen, Computer Science student)
- Profile: Budget $300-800, beginner tech level, student

### Script

**[NARRATOR]** "Let's meet Sarah, a computer science student looking for her first real development laptop."

**[ACTION]** Show Sarah's profile briefly
```
User: Sarah Chen
Budget: $300 - $800
Experience: Beginner
Goals: Coding, School Projects
```

**[NARRATOR]** "Watch how FinFind handles her vague request and applies her financial context automatically."

**[ACTION]** Type in search bar:
```
"I need a laptop for coding but I'm on a student budget"
```

**[PAUSE]** Wait for results (2-3 seconds)

**[NARRATOR]** "Notice several things happening here:"

**[POINT OUT]**
1. **Query Interpretation**: "The SearchAgent understood 'coding' means she needs good RAM, decent processor, and comfortable keyboard"
2. **Budget Application**: "It automatically filtered to her $300-800 budget range without her specifying exact numbers"
3. **Student Context**: "Results prioritize value and durability over premium features"

**[ACTION]** Hover over first result to show tooltip:
```
Match Score: 94%
- Within budget ✓
- Good for development ✓
- Student-friendly ✓
```

**[ACTION]** Click "Why this recommendation?" on top result

**[READ EXPLANATION]**
```
"This laptop matches your needs because:
✓ 16GB RAM handles multiple IDE instances
✓ $649 is well within your $800 budget
✓ SSD provides fast compilation times
✓ Highly rated by student developers"
```

**[NARRATOR]** "The ExplainabilityAgent provides clear reasoning, building trust with the user."

### Key Points to Emphasize
- No explicit budget number needed
- Context-aware interpretation
- Transparent explanations
- Personalized to user profile

---

## Scenario 2: Multi-Modal Search

### Setup
- Continue as Sarah or switch to demo user
- Have demo product image ready (screenshot of a MacBook)

### Script

**[NARRATOR]** "Now let's see FinFind's multi-modal capabilities. Sarah saw a laptop she liked at her friend's place but doesn't know the model."

**[ACTION]** Click the camera icon 📷 in search bar

**[ACTION]** Upload `demo/images/macbook_reference.jpg`

**[PAUSE]** Wait for image processing (2-3 seconds)

**[NARRATOR]** "The system analyzes the image and identifies key features..."

**[SHOW DETECTION]**
```
Detected: Laptop
Features: Slim design, silver color, premium build
Similar to: MacBook Air M2
Price Range: $999 - $1,299
```

**[NARRATOR]** "But these are over Sarah's budget. Watch what happens when she adds voice input."

**[ACTION]** Click microphone icon 🎤

**[SPEAK CLEARLY]** "but cheaper"

**[PAUSE]** Wait for voice processing

**[NARRATOR]** "The system combines the visual search with her voice query and budget constraints."

**[SHOW RESULTS]**
```
Similar Products in Your Budget:
1. ASUS ZenBook 14 - $699 (87% similar)
2. Lenovo IdeaPad Slim - $549 (82% similar)  
3. HP Pavilion Aero - $649 (79% similar)
```

**[ACTION]** Click on ASUS ZenBook to show comparison

**[NARRATOR]** "Each alternative shows what's similar and what's different from the original."

**[SHOW COMPARISON]**
```
vs. MacBook Air M2:
✓ Same: Slim design, lightweight, good display
≈ Similar: Build quality, keyboard
✗ Different: Operating system, ecosystem
💰 Savings: $500
```

### Key Points to Emphasize
- Seamless multi-modal input
- Image understanding
- Voice processing
- Intelligent alternative generation
- Budget-aware suggestions

---

## Scenario 3: Personalized Recommendations with Explanations

### Setup
- Login as: `demo_professional_001` (Marcus Johnson, Software Engineer)
- Profile: Budget $1,000-2,500, experienced, performance-focused

### Script

**[NARRATOR]** "Let's switch to Marcus, a software engineer with different needs and budget."

**[ACTION]** Show Marcus's profile:
```
User: Marcus Johnson
Budget: $1,000 - $2,500
Experience: Advanced
Goals: Professional Development, Performance
Preferences: Quality over cost
```

**[ACTION]** Navigate to "Recommendations" tab

**[NARRATOR]** "The RecommendationAgent has analyzed Marcus's profile and generated personalized suggestions."

**[SHOW RECOMMENDATIONS]**
```
Top Recommendations for You:

1. Dell XPS 15 Developer Edition - $1,849
   Match: 96% | "Perfect for your workflow"
   
2. ThinkPad X1 Carbon Gen 11 - $1,649
   Match: 93% | "Built for professional developers"
   
3. MacBook Pro 14" M3 - $1,999
   Match: 91% | "Premium performance option"
```

**[NARRATOR]** "Marcus wants to understand why the Dell is ranked #1."

**[ACTION]** Click "Why this?" button on Dell XPS

**[SHOW EXPLAINABILITY PANEL]**
```
Why Dell XPS 15 Developer Edition?

Profile Match Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Budget Fit        ████████████░░ 92%
Performance       █████████████░ 96%
Use Case Match    ██████████████ 100%
User Reviews      ████████████░░ 89%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key Reasons:
1. 32GB RAM matches your multi-tasking needs
2. Linux compatibility aligns with your dev preferences
3. Color-accurate display for your design work
4. Previous users with similar profiles rated it 4.8/5

Similar Users Also Considered:
- ThinkPad X1 Carbon (often compared)
- MacBook Pro 14" (premium alternative)
```

**[NARRATOR]** "This level of transparency builds trust and helps users make informed decisions."

**[ACTION]** Scroll to show "Learning" indicator

**[NARRATOR]** "Notice this learning indicator—as Marcus interacts, the system continuously improves its understanding."

### Key Points to Emphasize
- Profile-aware recommendations
- Transparent reasoning
- Multiple factors considered
- Continuous learning
- Trust through explainability

---

## Scenario 4: Out-of-Budget with Smart Alternatives

### Setup
- Login as: `demo_student_001` (Sarah) or continue
- Ensure budget constraint is active

### Script

**[NARRATOR]** "Let's see how FinFind handles when a user wants something beyond their means."

**[ACTION]** Type in search:
```
"MacBook Pro 16 inch for video editing"
```

**[PAUSE]** Wait for results

**[SHOW CONSTRAINT WARNING]**
```
⚠️ Budget Alert

The MacBook Pro 16" ($2,499) exceeds your budget of $800.

We found these alternatives that match your video editing needs:
```

**[NARRATOR]** "The AlternativeAgent immediately identifies the constraint violation and generates smart alternatives."

**[SHOW ALTERNATIVES]**
```
Smart Alternatives for Video Editing:

Within Your Budget ($300-800):
┌────────────────────────────────────────────┐
│ 1. ASUS VivoBook Pro 15 OLED - $799       │
│    Video Editing Score: 7.5/10            │
│    "Best value for video work"            │
│    Saves: $1,700                          │
├────────────────────────────────────────────┤
│ 2. Acer Aspire 5 Creator - $649           │
│    Video Editing Score: 6.8/10            │
│    "Solid entry-level option"             │
│    Saves: $1,850                          │
├────────────────────────────────────────────┤
│ 3. Lenovo IdeaPad Gaming 3 - $699         │
│    Video Editing Score: 7.2/10            │
│    "Gaming GPU helps with rendering"      │
│    Saves: $1,800                          │
└────────────────────────────────────────────┘

Stretch Budget Options ($800-1200):
If you can increase your budget slightly...
```

**[ACTION]** Click "Compare with Original"

**[SHOW COMPARISON]**
```
Feature Comparison: MacBook Pro vs ASUS VivoBook Pro

                    MacBook Pro 16"    ASUS VivoBook Pro
Price               $2,499             $799
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RAM                 18GB               16GB
Storage             512GB SSD          512GB SSD
Display             16.2" Liquid       15.6" OLED
GPU                 M3 Pro             RTX 3050
Video Score         9.5/10             7.5/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Trade-offs:
✗ Lower raw performance
✗ Windows vs macOS ecosystem
✓ $1,700 savings
✓ OLED display (better colors)
✓ Upgradeable RAM

Verdict: For a student starting out, the ASUS provides 
80% of the capability at 32% of the cost.
```

**[NARRATOR]** "Instead of just saying 'out of budget,' FinFind educates the user on their options and trade-offs."

### Key Points to Emphasize
- Proactive constraint detection
- Smart alternative generation
- Educational comparisons
- Respects user's financial reality
- Provides upgrade path information

---

## Demo Fallback: Pre-Recorded Video

If live demo fails:

1. **Have video ready** at `demo/backup_video.mp4`
2. **Announce**: "Let me show you a recording of the same flow"
3. **Play video** with narration
4. **Explain**: "The live system is available at [URL] for testing"

### Video Recording Tips
- Record at 1080p
- Use clean demo data
- Add cursor highlighting
- Include subtle captions
- Keep under 3 minutes
- Test playback before presentation

---

## Timing Guide

| Scenario | Target Time | Key Points |
|----------|-------------|------------|
| Setup & Intro | 30 sec | Set context |
| Scenario 1 | 90 sec | Vague query + budget |
| Scenario 2 | 90 sec | Multi-modal |
| Scenario 3 | 90 sec | Recommendations + explainability |
| Scenario 4 | 90 sec | Alternatives |
| **Total Demo** | **6 min** | Buffer included |

---

## Presenter Notes

### Do's
✅ Speak clearly and at moderate pace
✅ Point to specific UI elements
✅ Pause for key moments to sink in
✅ Have water nearby
✅ Practice 5+ times before

### Don'ts
❌ Rush through features
❌ Read from script verbatim
❌ Apologize for minor glitches
❌ Go off-script with unplanned features
❌ Assume audience knows technical terms

### Recovery Phrases
- "Let me show you that again..."
- "This is actually a good example of..."
- "As you can see, even with [issue], the system..."
- "Let's move to the next scenario while that loads..."
