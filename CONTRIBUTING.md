# Contributing to GamersPaperData

Thank you for helping build a community-maintained library of board game rules! This guide covers everything you need to add a new game or improve existing data.

## Repository Structure

```
GamersPaperData/
├── files/                    # Game data (one folder per game)
│   └── <game_id>/
│       ├── <game_id>_rules.json              # Required: Main rules file
│       ├── <game_id>_<cards>.json            # Optional: Card data files
│       ├── <game_id>_glossary.json           # Optional: Glossary terms
│       └── <game_id>_teaching_flow.json      # Optional: Interactive teaching walkthrough
├── icons/                    # SVG icons for game components
│   ├── README.md             # Icon catalog and usage guide
│   └── *.svg                 # Icon files
├── registry.json             # Game index (app fetches this to discover games)
├── CONTRIBUTING.md           # This file
└── README.md
```

## Quick Start: Adding a New Game

1. **Choose a game ID** — lowercase with underscores (e.g., `fox_in_the_forest`, `grand_austria_hotel`)
2. **Create the folder**: `files/<game_id>/`
3. **Create the rules file**: `files/<game_id>/<game_id>_rules.json`
4. **Optionally create card files**: `files/<game_id>/<game_id>_<card_type>.json`
5. **Register the game** in `registry.json`
6. **Open a pull request**

---

## JSON Schema Reference

### Rules File (`<game_id>_rules.json`)

#### Root Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `game_name` | string | **Yes** | Display name of the game |
| `designer` | string | **Yes** | Game designer(s) |
| `publisher` | string | **Yes** | Game publisher |
| `game_overview` | string | **Yes** | Full description of the game's theme and mechanics |
| `objective` | string | **Yes** | Primary win condition / goal |
| `min_players` | integer | **Yes** | Minimum supported player count |
| `max_players` | integer | **Yes** | Maximum supported player count |
| `bgg_link` | string | No | BoardGameGeek URL |
| `play_time_minutes` | integer | No | Average play time in minutes |
| `expansions` | array of [Expansion](#expansion-object) | No | Supported expansions |
| `components_overview` | array of [Component](#component-object) | No | List of game components |
| `setup` | array of [Phrase](#phrase-object) | No | Setup steps |
| `gameplay` | [Gameplay](#gameplay-object) | No | Turn structure and actions |
| `end_game` | [EndGame](#end-game-object) | No | End game triggers and scoring |
| `winning_condition` | string | No | Detailed winning conditions / tiebreakers |

---

### Phrase Object

The fundamental building block for rule text. Used in setup steps, action steps, notes, and more.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | **Yes** | The full rule text |
| `short_description` | string | No | Brief summary for compact views |
| `condition` | [Condition](#condition-object) | No | Player count / expansion filter (omit if rule always applies) |
| `action` | [PhraseAction](#phrase-action-object) | No | Interactive element (e.g., dice roll button) |

**Example:**
```json
{
  "description": "Shuffle the deck and deal 13 cards to each player.",
  "short_description": "Deal Cards"
}
```

---

### Condition Object

Controls when a rule, component, or card is visible based on player count or expansion.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `min_count_variant` | integer | No | Minimum player count for this item to appear |
| `max_count_variant` | integer | No | Maximum player count for this item to appear |
| `expansion` | string | No | Expansion ID this item belongs to (only shown when expansion is enabled) |

**Important rules:**
- **Omit the `"condition"` field entirely** if the rule applies to all player counts and the base game
- **NEVER put player count text** like "2 Players ONLY:" or "For 3-5 players:" in description text — use `condition` fields instead and let the app handle filtering

**Examples:**
```json
// Rule that applies ONLY to 2-player games
{
  "description": "Each player starts with 4 agents instead of 2.",
  "short_description": "Agent Count",
  "condition": { "min_count_variant": 2, "max_count_variant": 2 }
}

// Rule for 3 or more players
{
  "description": "Each player starts with 2 agents.",
  "short_description": "Agent Count",
  "condition": { "min_count_variant": 3 }
}

// Rule only for an expansion
{
  "description": "Add the expansion cards to the deck.",
  "condition": { "expansion": "promo_pack" }
}

// Rule that always applies (no condition needed)
{
  "description": "Place the board in the center of the table."
}
```

---

### Phrase Action Object

Adds interactive elements to phrases (e.g., a dice roll button or a card list link).

**Card List** (`type: "card_list"`):

Links a step or note to a card data file, rendering a tappable "Browse" chip that opens the card browser.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | string | **Yes** | — | Must be `"card_list"` |
| `value` | string | **Yes** | — | Filename of the card JSON file (e.g., `"my_game_round_cards.json"`) |
| `label` | string | No | `"Browse"` | Chip label text |

**Example:**
```json
{
  "description": "New action spaces are revealed each round via Round cards — one new space per round.",
  "short_description": "Round card spaces",
  "action": {
    "type": "card_list",
    "value": "agricola_round_cards.json",
    "label": "Browse"
  }
}
```

The referenced file must exist in the same game folder and follow the [Card File Schema](#card-file-schema-game_id_cardsjson).

---

**Dice Roll** (`type: "dice_roll"`):

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | string | **Yes** | — | Must be `"dice_roll"` |
| `min_value` | integer | No | `1` | Minimum die value |
| `max_value` | integer | No | `6` | Maximum die value |
| `use_player_count` | boolean | No | `false` | If `true`, rolls 1 to current player count |
| `label` | string | No | `"Roll"` | Button label text |

**Examples:**
```json
// Roll to determine start player (1 to player count)
{
  "description": "Randomly determine the start player.",
  "short_description": "First Player",
  "action": {
    "type": "dice_roll",
    "use_player_count": true,
    "label": "Player"
  }
}

// Standard d6 roll
{
  "description": "Roll to determine starting resources.",
  "action": {
    "type": "dice_roll",
    "min_value": 1,
    "max_value": 6
  }
}

// Custom range (e.g., a d8)
{
  "description": "Roll the d8 for event resolution.",
  "action": {
    "type": "dice_roll",
    "min_value": 1,
    "max_value": 8,
    "label": "Event"
  }
}
```

---

**Icon Formula** (`type: "icon_formula"`):

Renders a visual equation using inline icons from the shared icon registry. Icon tokens are wrapped in `{curly braces}`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | **Yes** | Must be `"icon_formula"` |
| `formula` | string | **Yes** | Formula string with `{IconName}` tokens (e.g., `"{TagD6} = {DiceQuestion}"`) |

**Example:**
```json
{
  "description": "Your dice determine which depot and estate spaces you can use.",
  "action": {
    "type": "icon_formula",
    "formula": "{TagD6} = {DiceQuestion}"
  }
}
```

Available icon names include: `Dice1`–`Dice6`, `DiceQuestion`, `Tag1`–`Tag6`, `TagD6`, `Pawn`, `Dollar`, `Hexagon`, `HexagonTile`, `Hourglass`, `TokensStack`, `Puzzle`, `ArrowRight`, `ArrowRotate`, `Card`, `CardsFan`, `HandCard`, `Hand`, `Sword`, `Shield`, `FlagTriangle`, `StructureHouse`, `Fire`, `CrownA`, `BookOpen`, `Award`, `TokenGive`, and all `Resource*` icons. See the app's icon registry for the full list.

---

**Value Grid** (`type: "value_grid"`):

Renders a compact reference table with dividers. Useful for scoring grids, phase bonuses, and other tabular data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | **Yes** | Must be `"value_grid"` |
| `columns` | array of arrays | **Yes** | Each inner array is one column of data. First element is the column header. |

**Example:**
```json
{
  "description": "Complete a region earlier for more bonus VP.",
  "action": {
    "type": "value_grid",
    "columns": [
      ["Phase", "A", "B", "C", "D", "E"],
      ["Bonus", "+10", "+8", "+6", "+4", "+2"]
    ]
  }
}
```

The grid auto-splits into multiple cards on narrow screens when column count exceeds available width.

---

### Component Object

Describes a physical game component (cards, tokens, boards, etc.).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | Component name |
| `type` | string | **Yes** | Component type (see list below) |
| `description` | string | **Yes** | What the component is |
| `subTypes` | array of strings | No | Component subtypes |
| `detailed_description` | string | No | Extended description |
| `icon` | string | No | Icon name from `icons/` (without `.svg`). See [icons/README.md](icons/README.md) |
| `count` | integer | No | How many of this component exist |
| `action` | [TriggerAction](#trigger-action-object) | No | Link to a card data file |
| `condition` | [Condition](#condition-object) | No | Player count / expansion filter |

**Component types** (flexible string values):
- `Board` — Game boards, player boards
- `Card` — Playing cards, action cards
- `Meeple` — Pawns, player pieces
- `Resource` — Tokens representing resources
- `Building` — Building tiles/tokens
- `Marker` — Score markers, turn markers
- `Token` — Generic tokens
- `Money` — Currency tokens/cards
- `Die` / `Dice` — Dice of any type

**Example with icon:**
```json
{
  "name": "Wheat Tokens",
  "type": "Resource",
  "description": "12 wheat resource tokens used for trading",
  "icon": "resource_wheat",
  "count": 12
}
```

**Example with card file link:**
```json
{
  "name": "Action Cards",
  "type": "Card",
  "subTypes": ["Attack", "Defense", "Support"],
  "description": "45 action cards used during gameplay",
  "action": {
    "name": "CardList",
    "value": "my_game_action_cards.json"
  }
}
```

**Player count variants:** If a component differs by player count, create separate entries:
```json
[
  {
    "name": "Agents",
    "type": "Meeple",
    "description": "Start with 4 agents. You do not gain an additional agent in round 5.",
    "condition": { "min_count_variant": 2, "max_count_variant": 2 }
  },
  {
    "name": "Agents",
    "type": "Meeple",
    "description": "Start with 2 agents. Gain an additional agent in round 5.",
    "condition": { "min_count_variant": 3 }
  }
]
```

---

### Trigger Action Object

Links a component to an external card data file.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | Currently must be `"CardList"` |
| `value` | string | **Yes** | Filename of the card JSON file (e.g., `"my_game_cards.json"`) |

The referenced file must exist in the same game folder.

---

### Gameplay Object

Describes the turn structure and available actions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `turn_structure` | string | **Yes** | A 2–3 sentence overview of how a round flows. Appears as the intro text on the Play screen. |
| `actions` | array of [GamePlayAction](#gameplay-action-object) | **Yes** | The **sequential phases of a round**, in the order they occur (e.g., "Phase 1: Draw Cards", "Phase 2: Take Actions", "Phase 3: Cleanup"). |
| `key_concepts` | array of [KeyConcept](#key-concept-object) | No | Important rules concepts |

---

### Gameplay Action Object

Each entry in `actions` represents **one phase of a round**, in the order it occurs. Within a phase where players choose from multiple options (e.g., a worker-placement game's action spaces, or a card game's available plays), list those options as `steps` inside that single phase entry rather than as separate top-level actions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | Phase name (e.g., `"Phase 1: Draw Cards"`, `"Work Phase"`, `"Harvest"`) |
| `description` | string | **Yes** | What happens during this phase |
| `steps` | array of [Phrase](#phrase-object) | **Yes** | Ordered sub-steps within the phase, or the available player choices if this is a selection phase |
| `notes` | array of [Phrase](#phrase-object) | No | Important exceptions or clarifications that don't fit in the sequential flow |
| `icon` | string | No | Icon name from the shared icon registry. Displayed on the action header. If omitted, a distinct fallback icon is assigned automatically. |

#### Common patterns

**Sequential phase game** (most games) — each phase is one entry:
```json
"actions": [
  {
    "name": "Phase 1: Draw Cards",
    "description": "Each player draws up to their hand limit.",
    "steps": [
      { "description": "Draw cards from the top of the deck until you have 5 in hand." }
    ],
    "notes": [
      { "description": "If the deck is empty, shuffle the discard pile to form a new deck." }
    ]
  },
  {
    "name": "Phase 2: Play Cards",
    "description": "In turn order, each player plays one card from their hand.",
    "steps": [
      { "description": "Choose a card from your hand and play it face-up." },
      { "description": "Resolve the card's effect immediately." }
    ],
    "notes": [
      { "description": "You must follow suit if able." },
      {
        "description": "Also draw a replacement card after playing.",
        "condition": { "min_count_variant": 2, "max_count_variant": 2 }
      }
    ]
  },
  {
    "name": "Phase 3: Cleanup",
    "description": "Discard played cards and pass the first-player token.",
    "steps": [
      { "description": "Move all played cards to the discard pile." },
      { "description": "Pass the first-player token clockwise." }
    ],
    "notes": []
  }
]
```

**Worker placement / action selection game** — the selection phase is one entry; the available action types are `steps` inside it:
```json
"actions": [
  {
    "name": "Phase 1: Place Workers",
    "description": "In turn order, each player places one worker on an unoccupied action space and takes that action. Continue until all workers are placed.",
    "steps": [
      { "description": "Gather resources: Take all tokens from the chosen resource space." },
      { "description": "Build: Pay the listed cost to construct a building on your board." },
      { "description": "Recruit: Pay 2 Food to add a new worker to your supply." }
    ],
    "notes": [
      { "description": "Only one player may occupy each space per round." }
    ]
  },
  {
    "name": "Phase 2: Return Home",
    "description": "Retrieve all workers and prepare for the next round.",
    "steps": [
      { "description": "Pick up all workers from the board and return them to your supply." }
    ],
    "notes": []
  }
]
```

---

### Key Concept Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | Concept name |
| `description` | string | **Yes** | Explanation of the concept |
| `action` | [PhraseAction](#phrase-action-object) | No | Optional visual element (e.g., a `value_grid` scoring table or `icon_formula`) |

**Example with a scoring grid:**
```json
{
  "name": "Phase Bonus (Timing)",
  "description": "Complete a region earlier for more bonus VP.",
  "action": {
    "type": "value_grid",
    "columns": [
      ["Phase", "A", "B", "C", "D", "E"],
      ["Bonus", "+10", "+8", "+6", "+4", "+2"]
    ]
  }
}
```

---

### End Game Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trigger` | string | No | What causes the game to end |
| `procedure` | array of strings | No | End-of-game steps |
| `intermediate_scoring` | array of [IntermediateScoring](#intermediate-scoring-object) | No | Mid-game scoring events that occur at specific points before the game ends |
| `final_scoring` | array of [FinalScoring](#final-scoring-object) | No | Scoring categories resolved at game end |

---

### Intermediate Scoring Object

Describes a scoring event that happens at a defined point **during** the game (e.g., after a specific round), rather than at the very end.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | **Yes** | Name of the scoring category or event |
| `when` | string | **Yes** | When this scoring occurs (e.g., `"Round 3"`, `"After Phase 2"`) |
| `description` | string | **Yes** | How points are calculated and any consequences |

---

### Final Scoring Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | **Yes** | Scoring category name |
| `description` | string | **Yes** | How points are calculated |

**Example:**
```json
{
  "end_game": {
    "trigger": "The game ends after 7 rounds.",
    "procedure": [
      "Complete round 7.",
      "Perform the final intermediate scoring.",
      "Proceed to Final Scoring."
    ],
    "intermediate_scoring": [
      {
        "source": "Mid-Game Bonus",
        "when": "Round 3",
        "description": "Score 1 VP per completed objective tile."
      },
      {
        "source": "Mid-Game Bonus",
        "when": "Round 5",
        "description": "Score 2 VP per completed objective tile."
      }
    ],
    "final_scoring": [
      {
        "source": "Trick Count",
        "description": "Score points based on tricks won: 0-3 tricks = 6 points, 4 tricks = 1 point, etc."
      },
      {
        "source": "Decree Cards",
        "description": "Add bonus points from any Decree cards won during play."
      }
    ]
  }
}
```

---

### Expansion Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | Unique expansion identifier (used in `condition.expansion`) |
| `name` | string | **Yes** | Display name of the expansion |

**Example:**
```json
{
  "expansions": [
    { "id": "promo_pack", "name": "Promo Pack" },
    { "id": "deluxe", "name": "Deluxe Edition" }
  ]
}
```

---

## Language Support

Games with official translations in multiple languages should use **language subfolders** to organize translated files.

### Folder Structure

The default language (English) lives in the root game folder. Translations go into language-specific subfolders using [ISO 639-1 language codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes):

```
files/<game_id>/
├── <game_id>_rules.json        # English (default)
├── <game_id>_cards.json
├── <game_id>_glossary.json
├── de/                          # German translation
│   ├── <game_id>_rules.json    # Same filename, different language
│   ├── <game_id>_cards.json
│   └── <game_id>_glossary.json
├── fr/                          # French translation
│   └── <game_id>_rules.json
└── es/                          # Spanish translation
    └── <game_id>_rules.json
```

**Key points:**
- Language subfolders use ISO 639-1 codes: `de`, `fr`, `es`, `it`, `ja`, `zh`, etc.
- Translated files use the **exact same filename** as the English version
- You can translate any combination of files (rules, cards, glossary)
- The app will automatically detect available languages from the folder structure

### Example: Faiyum

```
files/faiyum/
├── faiyum_rules.json           # English rules
├── faiyum_cards.json           # English cards
├── faiyum_glossary.json        # English glossary
└── de/
    └── faiyum_rules.json       # German rules translation
```

### Contributing Translations

When adding a translation:

1. Create the language subfolder if it doesn't exist: `files/<game_id>/<lang_code>/`
2. Copy the file(s) you're translating into the subfolder
3. Translate the content while preserving the JSON structure
4. Keep all field names in English (only translate values like `description`, `game_overview`, etc.)
5. Maintain the same `id` values for cards, components, and other referenced items

**What to translate:**
- User-facing text: `description`, `game_overview`, `objective`, `game_name`, etc.
- Card content, glossary definitions, setup steps, action descriptions

**What NOT to translate:**
- Field names (keep as `"description"`, not `"beschreibung"`)
- ID values (`"id": "worker"` stays the same in all languages)
- Icon references (`"icon": "Pawn"` stays the same)
- File references in `action.value` fields

---

## Glossary File Schema (`<game_id>_glossary.json`)

Optional glossary files define game-specific terminology. Useful for games with complex or thematic vocabulary.

**File structure**: Flat JSON object where keys are term IDs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | Unique identifier (must match the object key) |
| `name` | string | **Yes** | The term or phrase |
| `definition` | string | **Yes** | Clear explanation of the term |
| `related_terms` | array of strings | No | IDs of related glossary terms |
| `condition` | [Condition](#condition-object) | No | Player count / expansion filter |

**Example:**
```json
{
  "realignment": {
    "id": "realignment",
    "name": "Realignment",
    "definition": "An action where both players roll dice to attempt to remove opponent influence from a country. The higher roller (with modifiers) removes 1 opponent influence.",
    "related_terms": ["coup", "influence"]
  },
  "battleground": {
    "id": "battleground",
    "name": "Battleground Country",
    "definition": "A country marked with a star. Coups in battleground countries degrade DEFCON by 1. These countries are critical for regional Domination and Control.",
    "related_terms": ["defcon", "scoring"]
  }
}
```

---

## Card File Schema (`<game_id>_<cards>.json`)

Card files are flat JSON objects where keys are card IDs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | Unique identifier (must match the object key) |
| `name` | string | **Yes** | Card name |
| `body` | string | **Yes** | Complete card text |
| `summary` | string | **Yes** | Short summary for list views |
| `details` | string | No | Additional context or clarifications |
| `extra` | string | No | Bonus effects, VP values, etc. |
| `count` | integer | No | How many copies of this card exist |
| `condition` | [Condition](#condition-object) | No | Player count / expansion filter |

**Example:**
```json
{
  "swan_01": {
    "id": "swan_01",
    "name": "Swan",
    "body": "When played: draw 2 cards from the deck. Discard 1 card from your hand.",
    "summary": "Draw 2, discard 1",
    "details": "The drawn cards come from the main deck, not the discard pile.",
    "extra": "Worth 3 VP at end of game"
  },
  "fox_01": {
    "id": "fox_01",
    "name": "Fox",
    "body": "Swap the trump suit with the card under the draw pile.",
    "summary": "Change trump suit"
  }
}
```

**Critical rules:**
- Every key **must** be a valid card object — do NOT add `_comment`, `_note`, or metadata keys
- The `id` field **must** match its object key
- Card files are referenced from components via `"action": { "name": "CardList", "value": "filename.json" }`

---

## Language Support

Games with official translations in multiple languages should use **language subfolders** to organize translated files.

### Folder Structure

The default language (English) lives in the root game folder. Translations go into language-specific subfolders using [ISO 639-1 language codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes):

```
files/<game_id>/
├── <game_id>_rules.json        # English (default)
├── <game_id>_cards.json
├── <game_id>_glossary.json
├── de/                          # German translation
│   ├── <game_id>_rules.json    # Same filename, different language
│   ├── <game_id>_cards.json
│   └── <game_id>_glossary.json
├── fr/                          # French translation
│   └── <game_id>_rules.json
└── es/                          # Spanish translation
    └── <game_id>_rules.json
```

**Key points:**
- Language subfolders use ISO 639-1 codes: `de`, `fr`, `es`, `it`, `ja`, `zh`, etc.
- Translated files use the **exact same filename** as the English version
- You can translate any combination of files (rules, cards, glossary)
- The app will automatically detect available languages from the folder structure

### Example: Faiyum

```
files/faiyum/
├── faiyum_rules.json           # English rules
├── faiyum_cards.json           # English cards
├── faiyum_glossary.json        # English glossary
└── de/
    └── faiyum_rules.json       # German rules translation
```

### Contributing Translations

When adding a translation:

1. Create the language subfolder if it doesn't exist: `files/<game_id>/<lang_code>/`
2. Copy the file(s) you're translating into the subfolder
3. Translate the content while preserving the JSON structure
4. Keep all field names in English (only translate values like `description`, `game_overview`, etc.)
5. Maintain the same `id` values for cards, components, and other referenced items

**What to translate:**
- User-facing text: `description`, `game_overview`, `objective`, `game_name`, etc.
- Card content, glossary definitions, setup steps, action descriptions

**What NOT to translate:**
- Field names (keep as `"description"`, not `"beschreibung"`)
- ID values (`"id": "worker"` stays the same in all languages)
- Icon references (`"icon": "Pawn"` stays the same)
- File references in `action.value` fields

---

## Glossary File Schema (`<game_id>_glossary.json`)

Optional glossary files define game-specific terminology. Useful for games with complex or thematic vocabulary.

**File structure:** Flat JSON object where keys are term IDs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | Unique identifier (must match the object key) |
| `name` | string | **Yes** | The term or phrase |
| `definition` | string | **Yes** | Clear explanation of the term |
| `related_terms` | array of strings | No | IDs of related glossary terms |
| `condition` | [Condition](#condition-object) | No | Player count / expansion filter |

**Example:**
```json
{
  "administration": {
    "id": "administration",
    "name": "Administration",
    "definition": "An action that retrieves all cards from your personal discard pile back to your hand. Also determines turn order for the next round.",
    "related_terms": ["turn_order", "discard_pile"]
  },
  "pharaoh_track": {
    "id": "pharaoh_track",
    "name": "Pharaoh Track",
    "definition": "A track showing how much influence each player has with Pharaoh. Higher position grants benefits during gameplay and end-game scoring."
  }
}
```

---

## Registry (`registry.json`)

After creating your game files, add an entry to `registry.json`:

```json
{
  "id": "fox_in_the_forest",
  "name": "The Fox in the Forest",
  "designer": "Joshua Buergel",
  "publisher": "Renegade Game Studios"
}
```

The `id` must match the folder name under `files/`.

---

## Icons

Icons can be referenced in components using the `"icon"` field. The value is the icon filename without the `.svg` extension.

See [icons/README.md](icons/README.md) for:
- Full list of all available icons
- How to reference icons in your JSON
- How to contribute new icons

---

## Best Practices

### Large Card Sets (100+ Cards)

For games with extensive card lists (e.g., *Twilight Struggle* with 110 event cards, *Dominion* with 500+ kingdom cards):

**1. Split cards by category or deck:**
```
files/twilight_struggle/
  ├── twilight_struggle_rules.json
  ├── twilight_struggle_early_war.json    (35 cards)
  ├── twilight_struggle_mid_war.json      (42 cards)
  └── twilight_struggle_late_war.json     (23 cards)
```

**2. Reference multiple card files from components:**
```json
{
  "components_overview": [
    {
      "name": "Early War Cards",
      "type": "Card",
      "action": { "name": "CardList", "value": "twilight_struggle_early_war.json" }
    },
    {
      "name": "Mid War Cards",
      "type": "Card",
      "action": { "name": "CardList", "value": "twilight_struggle_mid_war.json" }
    }
  ]
}
```

**3. Include search-friendly fields:**
- `summary`: Short version for list views
- `category`, `type`, or `subType`: For filtering
- `tags`: Array of searchable keywords

**Example:**
```json
{
  "card_id": {
    "id": "card_id",
    "name": "Card Name",
    "body": "Full card text...",
    "summary": "Brief one-liner",
    "category": "Action",
    "tags": ["attack", "military", "one-time"]
  }
}
```

### Card-Driven Games

For card-driven games (where cards are the primary mechanism), **prioritize creating card data files**. Players reference cards more than rules during play.

**Minimum for card-driven games:**
1. Rules file with core mechanics
2. Card files with all playable cards
3. Component linking to card files

### Player Count Variants

**Do:**
- Use `condition` objects with `min_count_variant` / `max_count_variant`
- Create separate component entries for count-specific items
- Keep descriptions generic (no "2-player:" prefixes)

**Don't:**
- Put player count text in descriptions ("For 3-5 players:")
- Use inline conditionals ("If 2 players, X; otherwise Y")

Let the app filter by player count — your descriptions should read naturally for any applicable count.

---

## Complete Example: Minimal Game

```json
{
  "game_name": "Example Card Game",
  "designer": "Jane Designer",
  "publisher": "Example Games",
  "game_overview": "A fast trick-taking game for 2 players set in a magical forest.",
  "objective": "Score the most points by winning the right number of tricks.",
  "min_players": 2,
  "max_players": 2,
  "bgg_link": "https://boardgamegeek.com/boardgame/000000",
  "play_time_minutes": 30,
  "components_overview": [
    {
      "name": "Playing Cards",
      "type": "Card",
      "description": "33 cards numbered 1-11 in three suits",
      "icon": "cards_fan"
    },
    {
      "name": "Score Tokens",
      "type": "Token",
      "description": "Tokens for tracking score",
      "icon": "token"
    }
  ],
  "setup": [
    { "description": "Shuffle the deck and deal 13 cards to each player." },
    { "description": "Place the remaining 7 cards face-down as a draw pile." },
    { "description": "Flip the top card of the draw pile to determine the trump suit." }
  ],
  "gameplay": {
    "turn_structure": "Play proceeds in tricks. The lead player plays a card, then the other player responds.",
    "actions": [
      {
        "name": "Lead a Trick",
        "description": "If you won the previous trick (or are starting), play any card to lead.",
        "steps": [
          { "description": "Choose any card from your hand." },
          { "description": "Play it face-up to the center." }
        ]
      },
      {
        "name": "Follow a Trick",
        "description": "Play a card in response to the led card.",
        "steps": [
          { "description": "You must follow suit if able." },
          { "description": "If you cannot follow suit, play any card." }
        ],
        "notes": [
          { "description": "The higher card of the led suit wins, unless trump is played." }
        ]
      }
    ]
  },
  "end_game": {
    "trigger": "The game ends when all 13 tricks have been played.",
    "final_scoring": [
      {
        "source": "Tricks Won",
        "description": "0-3 tricks: 6 points. 4 tricks: 1 point. 5 tricks: 2 points. 6 tricks: 3 points. 7-9 tricks: 6 points. 10+ tricks: 0 points."
      }
    ]
  },
  "winning_condition": "The player with the most points wins. In case of a tie, the player who won fewer tricks wins."
}
```

---

## Teaching Flow File (`<game_id>_teaching_flow.json`)

Optional interactive walkthrough that teaches new players how to play. Appears as a "Learn" button on the game landing page.

**File structure:** A directed graph of nodes with a linear main path and optional side branches.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `game_id` | string | **Yes** | Must match the game's folder identifier |
| `start_node` | string | **Yes** | ID of the first node to display |
| `nodes` | array of [TeachingNode](#teaching-node-object) | **Yes** | All nodes in the flow |

### Teaching Node Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | Unique node identifier (`snake_case`) |
| `title` | string | **Yes** | Heading displayed above the content |
| `content` | array of [TeachingContent](#teaching-content-object) | **Yes** | Text and visual content items |
| `options` | array of [TeachingOption](#teaching-option-object) | **Yes** | Navigation buttons (at least one) |

### Teaching Content Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | **Yes** | The text to display |
| `style` | string | No | `"header"`, `"section"`, `"numbered"`, `"bullet"`, or `"body"` (default) |
| `glossary_ref` | string | No | Key into the game's glossary for icon/tint lookup |
| `icon` | string | No | Icon name (overrides glossary) |
| `tint` | string | No | Hex color (e.g. `"#2D5A27"`) or `"rainbow"` |
| `action` | object | No | `icon_formula`, `value_grid`, `dice_roll`, or `card_list` |
| `condition` | [Condition](#condition-object) | No | Player count / expansion filter |

### Teaching Option Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | **Yes** | Button text |
| `next_node` | string | No | Target node ID. `null` = end of flow (navigates back to game overview) |
| `condition` | [Condition](#condition-object) | No | Player count / expansion filter |

### Main Path vs. Side Branches

Teaching flows are **linear with optional detours**, not a maze.

- The **first option** in each node is the **main path** (rendered as a filled button)
- Subsequent options are **side branches** (rendered as outlined buttons with a help icon)
- `next_node: null` ends the flow and returns to the game overview

**Critical rule: side branches return to the parent node.** When a side branch node's "Got it" button navigates back, it must go to the **parent node** that offered the branch. This lets the learner explore other side branches or press the main-path button to continue forward.

```
Main path:  A ──→ B ──→ C ──→ D
                   ↑ ↓
Side branch: B offers "Details?" ──→ B2 ──→ B  (back to B, where "Got it" → C)
```

**Example:**
```json
// Parent node: key_actions
"options": [
  { "label": "Got it", "next_node": "the_harvest" },           // main path → C
  { "label": "How do animals work?", "next_node": "animals" }  // side branch → B2
]

// Side branch node: animals
"options": [
  { "label": "Got it", "next_node": "key_actions" }  // back to parent (where user can continue or explore)
]
```

### Design Guidelines

- **7–12 main path nodes** (3–5 minutes to complete)
- **2–4 content items per node** — more means the node teaches too much
- **One concept per node** — split unrelated concepts into separate nodes
- **Progressive disclosure** — start simple, add complexity through optional branches
- Write conversationally, not like a rulebook

### Action Types

**Icon Formula** — visual "equation" using game icons:
```json
{ "action": { "type": "icon_formula", "formula": "{Fire} + Sheep {ArrowRight} 2 Food" } }
```

**Value Grid** — table of values (e.g., scoring):
```json
{ "action": { "type": "value_grid", "columns": [["Tiles", "VP"], ["1", "1"], ["2", "3"]] } }
```

**Dice Roll** — interactive die roller:
```json
{ "action": { "type": "dice_roll", "min_value": 1, "max_value": 6, "label": "Roll" } }
```

**Card List** — link to browse a card data file:
```json
{ "action": { "type": "card_list", "value": "game_cards.json", "label": "View Cards" } }
```

---

## Validation Checklist

Before submitting a pull request:

- [ ] `game_id` folder name is lowercase with underscores
- [ ] All required fields are present in the rules file
- [ ] JSON is valid (no trailing commas, proper escaping)
- [ ] Card `id` fields match their object keys
- [ ] Player count variants use `"condition"` object with `min_count_variant` / `max_count_variant` — never player count text in descriptions
- [ ] All card files referenced by components actually exist in the game folder
- [ ] Component `type` values are consistent
- [ ] No placeholder or TODO text remains
- [ ] Teaching flow side branches return to the parent node (not skip ahead to the next main-path node)
- [ ] Teaching flow `start_node` exists in the nodes list and all `next_node` references resolve
- [ ] Game is registered in `registry.json` with matching `id`
- [ ] If adding translations, language subfolders use ISO 639-1 codes (`de/`, `fr/`, not `_de.json` suffixes)
- [ ] Translated files use the same filenames as English originals (in language subfolders)
- [ ] Field names remain in English; only translate user-facing content values

---

## Pull Request Process

1. Fork this repository
2. Create a branch (e.g., `add-game-fox-in-the-forest`)
3. Add your game files following the schema above
4. Verify your JSON is valid (use any JSON linter)
5. Run through the validation checklist
6. Open a pull request with a brief description of the game
