# Reasoning Viewer Component

## Overview

The **ReasoningViewer** component provides complete transparency into AI agent decision-making. It's designed to showcase that LLMs are performing genuine reasoning, not just generating random text.

## Purpose

This component addresses the "black box" problem in AI systems by showing:
- **What the agent saw** (input context)
- **What prompt was sent** to the LLM
- **How the LLM reasoned** (analysis, alternatives, risks)
- **What action was taken** (execution and validation)

## Features

### ✅ Full-Screen Modal Interface
- Dark theme with glassmorphism design
- Responsive and accessible
- Smooth animations

### ✅ 4-Tab Navigation
1. **Input Context** - What information the agent received
2. **LLM Interaction** - The exact prompt sent to GPT-4
3. **LLM Response** - Complete reasoning and analysis
4. **Execution** - Smart contract validation and blockchain recording

### ✅ Interactive Features
- Copy-to-clipboard for all code sections
- Export full reasoning as JSON
- Search within reasoning content
- Collapsible sections for long content
- Keyboard navigation support

### ✅ Educational Visualizations
- Confidence score meters
- Risk level indicators
- Smart contract validation checks
- Timeline of decision process
- Impact metrics

## Usage

### Basic Implementation

```tsx
import ReasoningViewer, { ReasoningData } from './components/ReasoningViewer';
import { useState } from 'react';

function MyComponent() {
  const [isOpen, setIsOpen] = useState(false);
  const [reasoningData, setReasoningData] = useState<ReasoningData | null>(null);

  return (
    <>
      <button onClick={() => setIsOpen(true)}>
        View Reasoning
      </button>

      {reasoningData && (
        <ReasoningViewer
          data={reasoningData}
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
```

### TypeScript Interface

```typescript
interface ReasoningData {
  // Agent identification
  agentId: string;
  agentName: string;
  agentRole: 'supply_chain' | 'financial' | 'facility' | 'decision_support';
  timestamp: string;

  // Tab 1: Input Context
  inputContext: {
    situation: {
      description: string;
      urgency: 'critical' | 'high' | 'medium' | 'low';
      affectedDepartments: string[];
    };
    constraints: Constraint[];
    historicalData: {
      similarCases: number;
      avgOutcome: string;
      successRate: number;
    };
    knowledgeBase: KnowledgeBaseEntry[];
  };

  // Tab 2: LLM Prompt
  llmPrompt: {
    systemMessage: string;
    userMessage: string;
    temperature: number;
    maxTokens: number;
    model: string;
  };

  // Tab 3: LLM Response
  llmResponse: {
    analysis: string;
    recommendedAction: string;
    confidence: number; // 0-1
    justification: string;
    alternatives: Alternative[];
    risks: string[];
    responseTimeMs: number;
    rawJSON: string;
  };

  // Tab 4: Execution
  executionResult: {
    actionTaken: string;
    smartContractValidation: SmartContractValidation;
    blockchainTx: {
      txHash: string;
      blockNumber: number;
      timestamp: string;
    };
    outcome: string;
    impact: {
      costSaved: number;
      timesSaved: number;
      efficiencyGain: number;
    };
  };

  // Footer
  escalationStatus: 'none' | 'human_review' | 'escalated';
  riskLevel: 'low' | 'medium' | 'high';
}
```

## Demo Page

Run the demo to see the component in action:

```bash
cd frontend
npm run dev
```

Then navigate to the ReasoningViewerDemo component to see sample data for:
- Supply Chain Agent (critical PPE shortage decision)
- Financial Agent (budget approval decision)

## Sample Data Structure

### Supply Chain Example

```typescript
const reasoningData: ReasoningData = {
  agentId: 'SC-001',
  agentName: 'Supply Chain Agent',
  agentRole: 'supply_chain',
  timestamp: '2025-10-12T20:45:33Z',

  inputContext: {
    situation: {
      description: 'Critical shortage of PPE supplies...',
      urgency: 'critical',
      affectedDepartments: ['Emergency', 'ICU', 'Surgical'],
    },
    constraints: [
      {
        agentName: 'Financial Agent',
        type: 'budget_constraint',
        value: { remaining: 2000, allocated: 5000 },
        priority: 'high',
      },
      // ... more constraints
    ],
    historicalData: {
      similarCases: 23,
      avgOutcome: 'Successfully resolved',
      successRate: 87,
    },
    knowledgeBase: [
      { key: 'min_threshold', value: 500, source: 'policy.json' },
      // ... more entries
    ],
  },

  llmPrompt: {
    systemMessage: 'You are an expert Supply Chain Agent...',
    userMessage: 'SITUATION: Critical PPE shortage...',
    temperature: 0.7,
    maxTokens: 2048,
    model: 'gpt-4-turbo-preview',
  },

  llmResponse: {
    analysis: 'Critical assessment shows...',
    recommendedAction: 'Order 800 PPE units...',
    confidence: 0.92,
    justification: 'This decision balances all constraints...',
    alternatives: [
      {
        action: 'Order 1,000 units',
        pros: ['Maximizes inventory buffer'],
        cons: ['Exceeds storage capacity'],
        confidence: 0.45,
      },
    ],
    risks: ['Delivery delay could create critical gap'],
    responseTimeMs: 1847,
    rawJSON: '{"analysis": "...", ...}',
  },

  executionResult: {
    actionTaken: 'Purchase order created: 800 units @ $1,600',
    smartContractValidation: {
      budgetCheck: true,
      storageCheck: true,
      confidenceCheck: true,
      complianceCheck: true,
      details: 'All policy constraints satisfied',
    },
    blockchainTx: {
      txHash: '0x7f8a3bc4...',
      blockNumber: 1847,
      timestamp: '2025-10-12T20:45:35Z',
    },
    outcome: 'Order successfully placed and recorded',
    impact: {
      costSaved: 400,
      timesSaved: 2.5,
      efficiencyGain: 23,
    },
  },

  escalationStatus: 'none',
  riskLevel: 'medium',
};
```

## Integration with Backend

To integrate with your backend agents:

```python
# backend/agents/agent_base.py

def reason_with_tracking(self, context):
    """Reason and return both decision and reasoning trace"""

    # Prepare prompt
    prompt = self._build_prompt(context)

    # Call LLM
    start_time = time.time()
    response = self.client.chat.completions.create(...)
    response_time = (time.time() - start_time) * 1000

    # Build reasoning data
    reasoning_data = {
        "agentId": self.name,
        "agentName": self.full_name,
        "agentRole": self.role,
        "timestamp": datetime.now().isoformat(),
        "inputContext": {
            "situation": context["situation"],
            "constraints": context["constraints"],
            "historicalData": self._get_historical_data(context),
            "knowledgeBase": self._get_relevant_kb_entries(context),
        },
        "llmPrompt": {
            "systemMessage": self.system_prompt,
            "userMessage": prompt,
            "temperature": 0.7,
            "maxTokens": 2048,
            "model": self.model,
        },
        "llmResponse": {
            "analysis": response["analysis"],
            "recommendedAction": response["action"],
            "confidence": response["confidence"],
            "justification": response["justification"],
            "alternatives": response["alternatives"],
            "risks": response["risks"],
            "responseTimeMs": response_time,
            "rawJSON": json.dumps(response),
        },
        # ... executionResult filled after action is taken
    }

    return response, reasoning_data
```

### API Endpoint

```python
# backend/api/routes.py

@app.route('/api/agents/<agent_id>/reasoning/<decision_id>', methods=['GET'])
def get_reasoning(agent_id, decision_id):
    """Get full reasoning trace for a decision"""
    reasoning = db.get_reasoning_trace(agent_id, decision_id)
    return jsonify(reasoning)
```

### Frontend Integration

```tsx
// Fetch reasoning from API
const fetchReasoning = async (agentId: string, decisionId: string) => {
  const response = await fetch(
    `/api/agents/${agentId}/reasoning/${decisionId}`
  );
  const data = await response.json();
  setReasoningData(data);
  setIsOpen(true);
};

// In your component
<button onClick={() => fetchReasoning('SC-001', '1847')}>
  View Reasoning
</button>
```

## Key Design Decisions

### 1. **Transparency Over Simplicity**
Show the raw prompts and responses - don't hide the "magic". This builds trust.

### 2. **Educational Focus**
The component is designed to teach users how AI agents work, not just show results.

### 3. **Technical but Accessible**
Uses syntax highlighting and proper terminology while remaining understandable.

### 4. **Complete Audit Trail**
Every piece of the decision-making process is captured and displayable.

## Styling Guidelines

The component uses:
- **Dark theme** (slate-900 background)
- **Glassmorphism** (backdrop-blur effects)
- **Color coding**:
  - Blue: Information and context
  - Green: Success and positive outcomes
  - Yellow: Warnings and medium risk
  - Red: Critical issues and high risk
  - Purple: Technical/blockchain data
- **Monospace fonts** for code and technical data
- **Sans-serif fonts** for explanatory text

## Keyboard Shortcuts

- `Tab` / `Shift+Tab` - Navigate between tabs
- `Esc` - Close modal
- `Cmd/Ctrl + F` - Focus search
- `Cmd/Ctrl + E` - Export JSON

## Accessibility

- ✅ Full keyboard navigation
- ✅ ARIA labels for screen readers
- ✅ Focus management
- ✅ Color contrast compliant
- ✅ Semantic HTML structure

## Performance

- **Lazy loading** - Only renders active tab content
- **Virtualization** - Long lists use virtual scrolling
- **Memoization** - Heavy computations cached
- **Code splitting** - Syntax highlighter loaded on demand

## Future Enhancements

### Comparison Mode
Compare two decisions side-by-side:
```tsx
<ReasoningViewer
  data={reasoningData}
  compareWith={otherReasoningData}
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
/>
```

### Timeline View
Show how long each step took:
- Context gathering: 50ms
- LLM reasoning: 1847ms
- Validation: 120ms
- Blockchain recording: 230ms

### Interactive Editing
Allow users to modify inputs and see how the decision would change.

## Testing

```bash
# Run component tests
npm test ReasoningViewer

# Run accessibility tests
npm run test:a11y

# Visual regression tests
npm run test:visual
```

## Files

- `ReasoningViewer.tsx` (1,008 lines) - Main component
- `ReasoningViewerDemo.tsx` (490 lines) - Demo page with sample data
- `REASONING_VIEWER.md` (this file) - Documentation

## Support

For questions or issues:
1. Check the demo page for examples
2. Review the TypeScript interfaces
3. See the sample data structures
4. Open an issue on GitHub

---

**Built with transparency in mind. Show the world that AI agents actually think!** 🧠
