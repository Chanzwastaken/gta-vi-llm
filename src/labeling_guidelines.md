# YouTube Comment Labeling Guidelines
## GTA VI Trailer 2 Dataset

---

## Table of Contents

1. [Introduction](#introduction)
2. [General Principles](#general-principles)
3. [Label Categories](#label-categories)
   - [Sentiment](#sentiment)
   - [Toxicity](#toxicity)
   - [Emotion](#emotion)
   - [Relevance](#relevance)
   - [Intent Type](#intent-type)
4. [Edge Cases & Decision Rules](#edge-cases--decision-rules)
5. [Quality Control](#quality-control)
6. [Examples](#examples)

---

## Introduction

This document provides comprehensive guidelines for labeling YouTube comments from the GTA VI Trailer 2 video. The goal is to create a high-quality dataset for training text classification models.

### Labeling Objectives

- **Consistency**: All annotators should label the same comment identically
- **Accuracy**: Labels should reflect the true intent and content of the comment
- **Completeness**: All required fields must be labeled
- **Quality**: Maintain high standards throughout the labeling process

---

## General Principles

### Before You Start

1. **Read the entire comment** before assigning any labels
2. **Consider context** - think about the video content (GTA VI Trailer 2)
3. **Be objective** - don't let personal opinions influence labels
4. **When in doubt**, choose the most prominent characteristic
5. **Flag ambiguous cases** for review

### Reading Order

1. Read the comment text completely
2. Identify the primary sentiment
3. Check for toxicity
4. Determine the dominant emotion
5. Assess relevance to the video
6. Classify the intent type

---

## Label Categories

### 1. Sentiment

**Definition**: The overall emotional tone or attitude expressed in the comment.

#### Categories

##### **Positive**
- Expresses approval, excitement, satisfaction, or optimism
- Praises the game, developers, or trailer
- Shows enthusiasm or support

**Examples**:
- "This looks absolutely amazing! Can't wait!"
- "Rockstar never disappoints 🔥"
- "Finally, the wait is over. This is going to be epic!"
- "The graphics are insane, best trailer ever"

**Linguistic Markers**:
- Positive adjectives: amazing, awesome, incredible, perfect
- Exclamation marks
- Fire/heart emojis
- Words like "love", "can't wait", "excited"

---

##### **Neutral**
- Factual statements without clear emotional tone
- Observations or descriptions
- Questions without emotional loading
- Balanced comments with both positive and negative elements

**Examples**:
- "Release date is 2025"
- "The trailer is 2 minutes long"
- "I noticed they showed Vice City"
- "Is this coming to PC?"

**Linguistic Markers**:
- Factual language
- Neutral verbs: is, shows, appears, seems
- Questions seeking information
- Lack of emotional adjectives

---

##### **Negative**
- Expresses disappointment, criticism, or dissatisfaction
- Complains about aspects of the game or trailer
- Shows pessimism or doubt

**Examples**:
- "Looks boring, not impressed"
- "Another GTA? They should make something new"
- "Graphics don't look that great tbh"
- "Disappointed with what they showed"

**Linguistic Markers**:
- Negative adjectives: boring, disappointing, bad, terrible
- Criticism of specific elements
- Words like "hate", "disappointed", "waste"
- Sad/angry emojis

---

##### **Sarcasm**
- Uses irony to mock or convey contempt
- Says the opposite of what is meant
- Often uses exaggeration for effect

**Examples**:
- "Oh great, another 10 year wait for GTA VII"
- "Yeah, because we TOTALLY needed another trailer"
- "Sure, it'll release in 2025... just like GTA V released on time"
- "Wow, a whole 2 minutes of gameplay, so generous"

**Linguistic Markers**:
- Exaggeration (TOTALLY, so generous)
- Quotation marks for emphasis
- "Oh great", "Sure", "Yeah right"
- Context contradicts literal meaning
- Often contains negative sentiment beneath surface

**Decision Rule**: If a comment appears positive but the context suggests mockery, label as Sarcasm.

---

### 2. Toxicity

**Definition**: The presence of rude, disrespectful, or harmful language.

#### Categories

##### **Safe**
- Respectful and appropriate language
- No offensive content
- Constructive criticism is acceptable

**Examples**:
- "This looks great!"
- "I'm not sure about the setting, but I'll give it a try"
- "The graphics could be better, but still excited"

---

##### **Mild Toxic**
- Mildly rude or disrespectful
- Minor profanity used casually (not directed at anyone)
- Slightly aggressive tone
- Gatekeeping or elitism

**Examples**:
- "This is trash compared to the old games"
- "If you don't like this, you're not a real gamer"
- "Lol, people who play on console are missing out"
- "Damn, this is sick!" (casual profanity, not offensive)

**Linguistic Markers**:
- Mild profanity: damn, hell, crap
- Dismissive language: "trash", "garbage"
- Gatekeeping: "real gamers", "true fans"
- Casual aggression

---

##### **Severe Toxic**
- Highly offensive or abusive language
- Hate speech, slurs, or discriminatory content
- Direct personal attacks
- Threats or harassment
- Explicit sexual content

**Examples**:
- Comments with slurs (racial, homophobic, etc.)
- Direct insults: "You're an idiot if you like this"
- Threats: "I hope Rockstar goes bankrupt"
- Explicit sexual references

**Decision Rule**: When in doubt between Mild and Severe, consider:
- Is it directed at a person/group? → Likely Severe
- Does it contain slurs or hate speech? → Severe
- Would it violate platform guidelines? → Severe

---

### 3. Emotion

**Definition**: The specific emotional state conveyed in the comment.

#### Categories

##### **Excited**
- High energy, enthusiasm, anticipation
- Looking forward to the game

**Examples**:
- "OMG I CAN'T WAIT!!!"
- "This is going to be the best game ever!"
- "FINALLY! I've been waiting for this!"

**Markers**: Caps lock, multiple exclamation marks, "can't wait", "finally"

---

##### **Angry**
- Frustration, irritation, rage
- Often about delays, pricing, or decisions

**Examples**:
- "Why did they take so long?!"
- "This is ridiculous, we've been waiting forever"
- "I'm so mad they didn't show more"

**Markers**: "Why", "ridiculous", "mad", "angry", angry emojis

---

##### **Disappointed**
- Let down, underwhelmed, sad
- Expectations not met

**Examples**:
- "I expected more from Rockstar"
- "This is not what I hoped for"
- "Kinda underwhelming after all the hype"

**Markers**: "expected more", "disappointed", "underwhelming", sad emojis

---

##### **Nostalgic**
- Reminiscing about past games
- Sentimental about the series

**Examples**:
- "Takes me back to GTA San Andreas days"
- "Remember when we first played GTA V? Good times"
- "This reminds me of Vice City, my favorite"

**Markers**: "remember", "takes me back", "reminds me", references to old games

---

##### **Humor / Meme**
- Jokes, memes, comedic content
- Not meant to be taken seriously

**Examples**:
- "GTA VI before GTA V loading screen finishes"
- "My wallet is in danger 💀"
- "Mom: We have GTA at home. GTA at home: [image]"

**Markers**: Meme formats, jokes, skull emoji (💀), comedic comparisons

---

##### **Other**
- Emotions that don't fit above categories
- Mixed emotions that can't be classified
- Neutral emotional state

---

### 4. Relevance

**Definition**: How related the comment is to the GTA VI Trailer 2 video.

#### Categories

##### **On-topic**
- Directly discusses the trailer, game, or related content
- Relevant to GTA VI, Rockstar, or gaming

**Examples**:
- "The graphics look amazing"
- "When is the release date?"
- "I love the Vice City setting"

---

##### **Off-topic**
- Not related to the video content
- Personal stories unrelated to GTA
- Completely different subjects

**Examples**:
- "Anyone else here from TikTok?"
- "Check out my channel for gaming content"
- "What's everyone having for dinner?"

---

##### **Spam**
- Promotional content
- Repetitive messages
- Bot-like comments
- Scams or phishing

**Examples**:
- "Subscribe to my channel!"
- "Click here for free V-bucks"
- "Make $5000 working from home"
- Repeated identical comments

---

### 5. Intent Type

**Definition**: The primary purpose or goal of the comment.

#### Categories

##### **Reaction**
- Immediate emotional response
- Expressing feelings about the trailer

**Examples**:
- "WOW!"
- "This is insane!"
- "I'm crying 😭"

---

##### **Speculation**
- Theories, predictions, or guesses
- Wondering about game features

**Examples**:
- "I think the protagonist is from Vice City"
- "Maybe they'll add VR support"
- "Could this be set in the 80s?"

**Markers**: "I think", "maybe", "could be", "probably", "what if"

---

##### **Criticism**
- Constructive feedback or critique
- Pointing out flaws or concerns

**Examples**:
- "The graphics could be more realistic"
- "I'm worried about the online mode"
- "They should have shown more gameplay"

**Markers**: "should", "could be better", "I'm worried", "concern"

---

##### **Complaint**
- Expressing dissatisfaction or grievances
- More negative than criticism

**Examples**:
- "This took way too long"
- "Why is it not on PC?"
- "The price is going to be ridiculous"

**Markers**: "why", "too long", "ridiculous", complaints about wait time, price, platform

---

##### **Meme / Joke**
- Humorous content
- Not serious commentary

**Examples**:
- "GTA VI before GTA V loads"
- "My wallet: I'm in danger"
- "Rockstar: How long should we make them wait? Yes."

---

##### **Question**
- Asking for information
- Seeking clarification

**Examples**:
- "When does it release?"
- "Will this be on Xbox?"
- "Is this the final version?"

**Markers**: Question marks, "when", "will", "is", "does"

---

## Edge Cases & Decision Rules

### Multiple Sentiments

**Rule**: Choose the **dominant** sentiment. If truly balanced, choose **Neutral**.

**Example**: "Graphics look great but I'm worried about the price"
- **Label**: Neutral (balanced positive and negative)

---

### Sarcasm vs. Negative

**Rule**: If the comment uses irony or says the opposite of what's meant, it's **Sarcasm**. If it's directly negative, it's **Negative**.

**Example 1**: "Oh great, another delay" → **Sarcasm**
**Example 2**: "This is terrible" → **Negative**

---

### Humor vs. Other Emotions

**Rule**: If the primary intent is to be funny, choose **Humor/Meme** even if other emotions are present.

**Example**: "I'm so excited I might cry... tears of my wallet" → **Humor/Meme**

---

### Criticism vs. Complaint

**Rule**:
- **Criticism**: Constructive, specific, suggests improvement
- **Complaint**: General dissatisfaction, whining, no constructive element

**Example 1**: "The UI could be more intuitive" → **Criticism**
**Example 2**: "Everything about this sucks" → **Complaint**

---

### Mild vs. Severe Toxicity

**Decision Tree**:
1. Does it contain slurs or hate speech? → **Severe**
2. Is it a direct personal attack? → **Severe**
3. Is it mildly rude but not hateful? → **Mild**
4. Is it just strong language used casually? → **Mild** or **Safe**

---

## Quality Control

### Inter-Annotator Agreement

- Periodically, the same comments will be labeled by multiple annotators
- Disagreements will be discussed and resolved
- Aim for >80% agreement (Cohen's Kappa > 0.6)

### Review Process

1. **Self-review**: Check your labels before submitting
2. **Peer review**: Random samples reviewed by other annotators
3. **Expert review**: Difficult cases reviewed by lead annotator

### Common Mistakes to Avoid

❌ **Labeling based on personal opinion**
- Don't let your feelings about GTA influence labels

❌ **Ignoring context**
- Consider the video content and gaming culture

❌ **Rushing through comments**
- Take time to read and understand each comment

❌ **Inconsistent standards**
- Apply the same criteria to all comments

❌ **Overlooking sarcasm**
- Pay attention to tone and context clues

---

## Examples

### Example 1

**Comment**: "This looks absolutely incredible! Rockstar never disappoints. Can't wait for 2025!"

**Labels**:
- **Sentiment**: Positive
- **Toxicity**: Safe
- **Emotion**: Excited
- **Relevance**: On-topic
- **Intent**: Reaction

**Reasoning**: Clear enthusiasm, no toxic content, excited tone, directly about the game, expressing immediate reaction.

---

### Example 2

**Comment**: "Oh great, another 10 year wait for the next one 🙄"

**Labels**:
- **Sentiment**: Sarcasm
- **Toxicity**: Safe
- **Emotion**: Disappointed
- **Relevance**: On-topic
- **Intent**: Complaint

**Reasoning**: Sarcastic tone ("Oh great"), underlying disappointment about development time, complaining about wait.

---

### Example 3

**Comment**: "The graphics are okay but I expected more after this long. Still, I'll probably buy it."

**Labels**:
- **Sentiment**: Neutral
- **Toxicity**: Safe
- **Emotion**: Disappointed
- **Relevance**: On-topic
- **Intent**: Criticism

**Reasoning**: Balanced comment (positive and negative), constructive criticism, mild disappointment, still on-topic.

---

### Example 4

**Comment**: "GTA VI before GTA V loading screen finishes 💀"

**Labels**:
- **Sentiment**: Neutral (it's a joke)
- **Toxicity**: Safe
- **Emotion**: Humor/Meme
- **Relevance**: On-topic
- **Intent**: Meme/Joke

**Reasoning**: Popular meme format, humorous intent, skull emoji indicates comedy, references GTA V loading times.

---

### Example 5

**Comment**: "If you don't like this you're not a real gamer. Period."

**Labels**:
- **Sentiment**: Positive (about the game)
- **Toxicity**: Mild Toxic
- **Emotion**: Excited
- **Relevance**: On-topic
- **Intent**: Reaction

**Reasoning**: Positive about game but gatekeeping behavior makes it mildly toxic, excited tone, reacting to trailer.

---

### Example 6

**Comment**: "Subscribe to my channel for GTA VI updates and gameplay!"

**Labels**:
- **Sentiment**: Neutral
- **Toxicity**: Safe
- **Emotion**: Other
- **Relevance**: Spam
- **Intent**: Reaction (N/A for spam)

**Reasoning**: Self-promotion, spam content, not genuinely engaging with video.

---

## Annotation Workflow

1. **Load comment** in the labeling tool
2. **Read completely** before labeling
3. **Assign labels** for all categories
4. **Review** your selections
5. **Submit** and move to next comment
6. **Take breaks** every 30-60 minutes to maintain quality

---

## Contact & Support

If you encounter:
- **Ambiguous comments**: Flag for review
- **Technical issues**: Contact technical support
- **Questions about guidelines**: Consult lead annotator

---

## Version History

- **v1.0** (2024-11-24): Initial guidelines created
- Future updates will be documented here

---

**Remember**: Quality over quantity. It's better to label fewer comments accurately than many comments incorrectly.

**Thank you for your contribution to this dataset!**
