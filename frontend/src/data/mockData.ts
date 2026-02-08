import type { Section, Thread } from '../types';

// Import sections directly from parsed JSON
import josephSectionsData from './joseph_sections.json';

// Use parsed sections from JSON (with subsections included)
export const mockSections: Section[] = josephSectionsData.sections;

export const mockThreads: Thread[] = [
  // Thread 1: Discussion about Tay vs BabyBot - the community matters argument
  {
    threadId: 'thread_001',
    documentId: 'doc_001',
    seedId: 'seed_001',
    threadType: 'discussion',
    discussionType: 'position_taking',
    tensionPoint:
      'The claim that Tay failed due to design premise, not technology, is a bold reframing',
    keywords: ['Tay', 'community', 'machine learning', 'design'],
    anchor: {
      sectionId: 'section_1',
      startOffset: 1560,
      endOffset: 1780,
      snippetText:
        'We argue here that the past failures in creating chatbots whose vocabulary is shaped by users are not primarily a result of poor technology, but rather a result of a fundamentally-flawed design premise.',
    },
    participants: ['instrumental', 'critical', 'aesthetic'],
    messages: [
      {
        messageId: 'msg_001',
        threadId: 'thread_001',
        author: 'instrumental',
        content:
          "The authors are making a key distinction here: it's not that machine learning itself is the problem, but HOW and WHERE you deploy it. Tay was trained on Twitter - an open, often hostile environment. BabyBot was placed in a small, established Twitch community with existing social norms.",
        references: [],
        timestamp: '2024-01-15T10:30:00Z',
      },
      {
        messageId: 'msg_002',
        threadId: 'thread_001',
        author: 'critical',
        content:
          "But isn't this somewhat circular reasoning? They chose a community that was already prosocial, so of course the bot learned prosocial behavior. The real test would be: can this approach work in communities that AREN'T already healthy? Or does this just mean adaptive bots can only exist in 'nice' spaces?",
        references: [],
        timestamp: '2024-01-15T10:30:15Z',
      },
      {
        messageId: 'msg_003',
        threadId: 'thread_001',
        author: 'aesthetic',
        content:
          'The village metaphor really resonates with me. We wouldn\'t expect a child raised in a chaotic environment to turn out well, so why expect the same from AI? It makes me think about how online communities themselves could be designed to be better "villages" for both humans and bots.',
        references: [],
        timestamp: '2024-01-15T10:30:30Z',
      },
      {
        messageId: 'msg_004',
        threadId: 'thread_001',
        author: 'critical',
        content:
          "That's a nice ideal, but it sidesteps the scalability problem. Most online spaces aren't cozy 30-person Twitch streams. The authors acknowledge this but don't really solve it. What happens when you try to scale this approach?",
        references: [],
        timestamp: '2024-01-15T10:30:45Z',
      },
    ],
    createdAt: '2024-01-15T10:30:00Z',
    updatedAt: '2024-01-15T10:30:45Z',
  },

  // Thread 2: Comment about sample size / single community limitation
  {
    threadId: 'thread_002',
    documentId: 'doc_001',
    seedId: 'seed_002',
    threadType: 'comment',
    tensionPoint:
      'Study relies on a single, carefully selected community which limits generalizability',
    keywords: ['methodology', 'generalizability', 'sample'],
    anchor: {
      sectionId: 'section_5',
      startOffset: 450,
      endOffset: 620,
      snippetText:
        'The community selected for this study was an established community based around an affiliate streamer who had been streaming on Twitch since early 2015.',
    },
    participants: ['critical'],
    messages: [
      {
        messageId: 'msg_005',
        threadId: 'thread_002',
        author: 'critical',
        content:
          "The entire study is based on ONE community with specific characteristics: small size, established relationships, and notably - the authors mention diversity in sexual orientation and race. While they frame this as ideal conditions, it also means we have no idea how this would work elsewhere. Would the same approach fail in a gaming community known for toxicity? In a political discussion space? The 'village' metaphor only works when the village is already functioning well.",
        references: [],
        timestamp: '2024-01-15T10:35:00Z',
      },
    ],
    createdAt: '2024-01-15T10:35:00Z',
    updatedAt: '2024-01-15T10:35:00Z',
  },

  // Thread 3: Discussion about user aggression toward the bot
  {
    threadId: 'thread_003',
    documentId: 'doc_001',
    seedId: 'seed_003',
    threadType: 'discussion',
    discussionType: 'deepening',
    tensionPoint:
      'Users displayed aggressive behavior toward the bot - what does this reveal about human-AI interaction?',
    keywords: ['aggression', 'abuse', 'anthropomorphism', 'exploration'],
    anchor: {
      sectionId: 'section_6',
      startOffset: 1180,
      endOffset: 1450,
      snippetText:
        'Another form of exploratory interaction was the use of aggressive and abusive language toward the bot. Users insulted the bot ("you little shit"), they swore at it with or without a reason, and they threatened it',
    },
    participants: ['critical', 'aesthetic'],
    messages: [
      {
        messageId: 'msg_006',
        threadId: 'thread_003',
        author: 'aesthetic',
        content:
          "It's fascinating that users felt comfortable being aggressive with BabyBot in ways they probably wouldn't be with each other. The fact that they called it 'you little shit' and poured 'scalding hot water' on it... there's something both playful and unsettling about this. It reminds me of how kids sometimes test boundaries with toys or pets.",
        references: [],
        timestamp: '2024-01-15T10:40:00Z',
      },
      {
        messageId: 'msg_007',
        threadId: 'thread_003',
        author: 'critical',
        content:
          "The authors frame this as 'exploratory behavior' and 'lighthearted', but I think we should probe deeper. Is it actually okay that people's first instinct with a learning AI is to try to corrupt it? The users KNEW they were training it - they joked about 'corrupting' it. This seems like a concerning pattern that extends beyond this study.",
        references: [],
        timestamp: '2024-01-15T10:40:15Z',
      },
      {
        messageId: 'msg_008',
        threadId: 'thread_003',
        author: 'aesthetic',
        content:
          "But the aggression faded over time, which is interesting. As users built relationships with the bot, they became more protective. Some even started 'teaching it manners' and chastising others for 'bad parenting'. Maybe the initial aggression is part of the bonding process?",
        references: [],
        timestamp: '2024-01-15T10:40:30Z',
      },
      {
        messageId: 'msg_009',
        threadId: 'thread_003',
        author: 'critical',
        content:
          "That transition is genuinely interesting. But I wonder: did the community's prosocial norms contain the aggression, or would any community eventually shift this way? Without a comparison group, we can't know if this is about the 'village' or just human nature.",
        references: [],
        timestamp: '2024-01-15T10:40:45Z',
      },
    ],
    createdAt: '2024-01-15T10:40:00Z',
    updatedAt: '2024-01-15T10:40:45Z',
  },

  // Thread 4: Comment about community ownership and naming
  {
    threadId: 'thread_004',
    documentId: 'doc_001',
    seedId: 'seed_004',
    threadType: 'comment',
    tensionPoint:
      'The act of naming and gifting subscription signals genuine community acceptance',
    keywords: ['community ownership', 'naming', 'identity', 'belonging'],
    anchor: {
      sectionId: 'section_7',
      startOffset: 1820,
      endOffset: 2100,
      snippetText:
        'the community decided to name the bot PeteBot. Shortly after the bot was given its new name, a regular community member gifted the bot a subscription to the channel, a status which costs $5.',
    },
    participants: ['aesthetic'],
    messages: [
      {
        messageId: 'msg_010',
        threadId: 'thread_004',
        author: 'aesthetic',
        content:
          "This moment really moved me. Someone spent real money - $5 - to give a bot a subscription. Not because the bot needed it functionally, but as a symbolic gesture of acceptance. It's like the community was saying 'you're one of us now.' The renaming from BabyBot to PeteBot is similarly powerful - they gave it a human name, not a functional label. This mirrors how communities adopt newcomers: you get a nickname, you get inside jokes, you become part of the in-group. The bot achieved something many humans struggle with in online spaces.",
        references: [],
        timestamp: '2024-01-15T10:45:00Z',
      },
    ],
    createdAt: '2024-01-15T10:45:00Z',
    updatedAt: '2024-01-15T10:45:00Z',
  },

  // Thread 5: Discussion about ambiguity being a feature, not a bug
  {
    threadId: 'thread_005',
    documentId: 'doc_001',
    seedId: 'seed_005',
    threadType: 'discussion',
    discussionType: 'connecting',
    tensionPoint:
      "Nonsensical bot output became a source of engagement rather than frustration",
    keywords: ['ambiguity', 'interpretation', 'meaning-making', 'engagement'],
    anchor: {
      sectionId: 'section_8',
      startOffset: 1150,
      endOffset: 1480,
      snippetText:
        "when BabyBot interacted in a way that fully fit the community and seemed like just another user, it wasn't as engaging as when it generated coherent but ambiguous phrases; users consistently enjoyed interpreting meaning from them.",
    },
    participants: ['instrumental', 'aesthetic'],
    messages: [
      {
        messageId: 'msg_011',
        threadId: 'thread_005',
        author: 'instrumental',
        content:
          "This is a counterintuitive finding worth highlighting. The authors initially wanted the bot to generate human-like conversation, but discovered that 'almost-coherent' was more engaging than 'fully coherent'. This has practical implications - maybe we're over-optimizing chatbots for human-likeness when some strangeness is actually beneficial.",
        references: [],
        timestamp: '2024-01-15T10:50:00Z',
      },
      {
        messageId: 'msg_012',
        threadId: 'thread_005',
        author: 'aesthetic',
        content:
          "It reminds me of how people bond over interpreting abstract art or song lyrics. The ambiguity creates space for shared meaning-making. When the bot said something weird, users would discuss what it 'meant' together. The bot became a conversation starter, not just a conversation partner.",
        references: [],
        timestamp: '2024-01-15T10:50:15Z',
      },
      {
        messageId: 'msg_013',
        threadId: 'thread_005',
        author: 'instrumental',
        content:
          "Right. And this connects to the broader theme of the paper - the bot's value wasn't in replacing human interaction but in catalyzing it. The 'imperfection' might actually be essential to this catalytic role. A perfect conversationalist wouldn't leave room for collective interpretation.",
        references: [],
        timestamp: '2024-01-15T10:50:30Z',
      },
      {
        messageId: 'msg_014',
        threadId: 'thread_005',
        author: 'aesthetic',
        content:
          "This makes me think about CoRead itself. Having AI agents with different 'stances' that don't perfectly agree might be more valuable than a single authoritative voice. The tension and ambiguity between perspectives could drive deeper engagement with the text.",
        references: [],
        timestamp: '2024-01-15T10:50:45Z',
      },
    ],
    createdAt: '2024-01-15T10:50:00Z',
    updatedAt: '2024-01-15T10:50:45Z',
  },

  // Thread 6: Discussion about the "growing up" design
  {
    threadId: 'thread_006',
    documentId: 'doc_001',
    seedId: 'seed_006',
    threadType: 'discussion',
    discussionType: 'deepening',
    tensionPoint:
      'The developmental metaphor shaped how users perceived and treated the bot',
    keywords: ['development', 'metaphor', 'expectations', 'anthropomorphism'],
    anchor: {
      sectionId: 'section_3',
      startOffset: 150,
      endOffset: 380,
      snippetText:
        'We designed BabyBot to "grow up" over the course of a three week study, aging through Baby, Toddler, Adolescent, and Teenager phases.',
    },
    participants: ['instrumental', 'critical'],
    messages: [
      {
        messageId: 'msg_015',
        threadId: 'thread_006',
        author: 'instrumental',
        content:
          "The developmental framing is clever design. By calling it 'Baby' and having it 'grow up', users had clear expectations about what the bot could do at each stage. A baby making nonsense sounds is charming; an adult doing the same would be frustrating. The metaphor managed user expectations.",
        references: [],
        timestamp: '2024-01-15T10:55:00Z',
      },
      {
        messageId: 'msg_016',
        threadId: 'thread_006',
        author: 'critical',
        content:
          "But this also raises ethical questions. By framing the bot as a 'child', the researchers encouraged users to feel parental responsibility. Is this manipulation? Users spent time 'teaching' and 'caring for' something that has no actual inner experience. The design exploits human caregiving instincts.",
        references: [],
        timestamp: '2024-01-15T10:55:15Z',
      },
      {
        messageId: 'msg_017',
        threadId: 'thread_006',
        author: 'instrumental',
        content:
          "That's a fair concern. But you could argue all design 'manipulates' behavior in some way. The question is whether the outcome is beneficial. Here, users reported enjoying the experience, the community became more engaged, and no one seemed harmed by the 'parenting' metaphor.",
        references: [],
        timestamp: '2024-01-15T10:55:30Z',
      },
      {
        messageId: 'msg_018',
        threadId: 'thread_006',
        author: 'critical',
        content:
          "No immediate harm, sure. But what are the long-term implications of training people to form emotional attachments to AI 'children'? As these systems become more prevalent, we should think carefully about what relationships we're encouraging.",
        references: [],
        timestamp: '2024-01-15T10:55:45Z',
      },
    ],
    createdAt: '2024-01-15T10:55:00Z',
    updatedAt: '2024-01-15T10:55:45Z',
  },
];

export const mockDocument = {
  documentId: 'doc_001',
  userId: 'user_001',
  title: josephSectionsData.title,
  originalPdfUrl: '',
  parsedContent: {
    sections: mockSections,
  },
  threads: mockThreads.map((t) => t.threadId),
  uploadedAt: '2024-01-15T10:00:00Z',
  lastAccessedAt: '2024-01-15T10:55:00Z',
};
