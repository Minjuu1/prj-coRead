import type { Section, Thread } from '../types';

export const mockSections: Section[] = [
  {
    sectionId: 'section_0',
    title: 'Abstract',
    content: `This study investigates the challenges undergraduate students face when engaging with academic texts. Through a mixed-methods approach involving 45 participants, we examine how students approach critical reading tasks and identify key barriers to deep comprehension. Our findings reveal that students often struggle with critical analysis of academic texts, tending to focus on surface-level understanding rather than engaging with the underlying arguments and assumptions. We propose a framework for scaffolded reading instruction that addresses these challenges.`,
    order: 0,
  },
  {
    sectionId: 'section_1',
    title: 'Introduction',
    content: `Academic reading is a fundamental skill for success in higher education. However, many undergraduate students enter university unprepared for the demands of scholarly texts. Previous research has shown that effective academic reading requires not only comprehension of content but also the ability to critically evaluate arguments, identify assumptions, and connect ideas across texts.

Our study reveals that students often struggle with critical analysis of academic texts. This difficulty manifests in several ways: students may accept claims without questioning evidence, fail to recognize implicit assumptions, or struggle to synthesize information from multiple sources. These challenges are particularly acute for first-generation college students and those from non-English speaking backgrounds.

The purpose of this study is to understand the specific barriers students face and to develop interventions that support deeper engagement with academic texts. We adopt a sociocultural perspective that views reading as a situated practice shaped by disciplinary norms and expectations.`,
    order: 1,
  },
  {
    sectionId: 'section_2',
    title: 'Methods',
    content: `We recruited 45 participants from undergraduate courses across three disciplines: psychology, biology, and history. Participants ranged from first-year to senior students, with a mean age of 20.3 years. The sample included 28 female and 17 male students, with 12 identifying as first-generation college students.

Data collection involved three components: (1) think-aloud protocols during reading tasks, (2) semi-structured interviews about reading strategies, and (3) analysis of annotated texts. Participants were asked to read and respond to two academic articles typical of their discipline.

Qualitative data were analyzed using thematic analysis following Braun and Clarke's six-phase approach. Two researchers independently coded transcripts, achieving an inter-rater reliability of 0.85. Quantitative measures of reading comprehension were analyzed using descriptive statistics and correlation analysis.`,
    order: 2,
  },
  {
    sectionId: 'section_3',
    title: 'Results',
    content: `Our analysis revealed three primary themes related to students' reading challenges:

Theme 1: Surface-Level Processing
The majority of students (78%) demonstrated a tendency toward surface-level processing, focusing on extracting facts rather than evaluating arguments. Students frequently reported feeling overwhelmed by academic vocabulary and complex sentence structures.

Theme 2: Limited Critical Questioning
Only 23% of students spontaneously questioned the claims or evidence presented in the texts. When prompted, many students expressed uncertainty about what constitutes valid criticism of academic work, with comments such as "Who am I to question the expert?"

Theme 3: Disconnected Reading
Students rarely connected reading to their own experiences or prior knowledge. Reading was often viewed as a task to complete rather than an opportunity for intellectual engagement. This was particularly evident in students' annotations, which tended to focus on definitions rather than reactions or questions.

Correlation analysis revealed significant relationships between critical reading behaviors and academic performance (r = 0.67, p < 0.001), suggesting that reading skills are indeed predictive of broader academic success.`,
    order: 3,
  },
  {
    sectionId: 'section_4',
    title: 'Discussion',
    content: `Our findings highlight the need for explicit instruction in critical reading strategies. The prevalence of surface-level processing suggests that students may not understand what deeper engagement looks like or may lack the strategies to achieve it.

The reluctance to question academic texts points to broader issues of academic identity and authority. Students may need support in developing the confidence to position themselves as legitimate participants in scholarly discourse.

Several limitations should be noted. First, our sample was drawn from a single institution, limiting generalizability. Second, the think-aloud methodology may have altered natural reading behaviors. Third, disciplinary differences in reading practices were not fully explored.

Future research should investigate the effectiveness of specific interventions, including collaborative reading activities, explicit strategy instruction, and the use of AI-assisted tools to scaffold critical analysis. Longitudinal studies tracking the development of reading skills across the undergraduate years would also be valuable.`,
    order: 4,
  },
];

export const mockThreads: Thread[] = [
  {
    threadId: 'thread_001',
    documentId: 'doc_001',
    seedId: 'seed_001',
    threadType: 'discussion',
    discussionType: 'position_taking',
    tensionPoint: 'The definition of "critical analysis" is unclear and may be interpreted differently',
    keywords: ['critical analysis', 'definition', 'students'],
    anchor: {
      sectionId: 'section_1',
      startOffset: 387,
      endOffset: 475,
      snippetText: 'Our study reveals that students often struggle with critical analysis of academic texts.',
    },
    participants: ['instrumental', 'critical', 'aesthetic'],
    messages: [
      {
        messageId: 'msg_001',
        threadId: 'thread_001',
        author: 'instrumental',
        content: "Looking at how the authors describe 'critical analysis difficulties,' they seem to mean students stay at the surface level - accepting claims without questioning evidence, missing implicit assumptions, and having trouble synthesizing across sources. This gives us a clear operational definition to work with.",
        references: [],
        timestamp: '2024-01-15T10:30:00Z',
      },
      {
        messageId: 'msg_002',
        threadId: 'thread_001',
        author: 'critical',
        content: "But here's the problem - the authors don't explicitly define what 'critical analysis' means to them. Are they talking about logical analysis? Questioning methodology? Ideological critique? These are very different things, and the paper conflates them. Without a clear definition, how can we evaluate whether their interventions would actually help?",
        references: [],
        timestamp: '2024-01-15T10:30:15Z',
      },
      {
        messageId: 'msg_003',
        threadId: 'thread_001',
        author: 'aesthetic',
        content: "This resonates with my own experience as a student. I remember feeling like 'being critical' meant finding something wrong with what I read, which felt uncomfortable when reading experts. Maybe the confusion about what critical analysis means is part of why students struggle - they don't have a clear model of what good critical reading looks like.",
        references: [],
        timestamp: '2024-01-15T10:30:30Z',
      },
      {
        messageId: 'msg_004',
        threadId: 'thread_001',
        author: 'instrumental',
        content: "Good point. The Methods section does operationalize it through specific behaviors they coded for. But @Critical is right that the theoretical framework could be clearer. This matters for replication and for instructors trying to apply these findings.",
        references: [],
        timestamp: '2024-01-15T10:30:45Z',
      },
    ],
    createdAt: '2024-01-15T10:30:00Z',
    updatedAt: '2024-01-15T10:30:45Z',
  },
  {
    threadId: 'thread_002',
    documentId: 'doc_001',
    seedId: 'seed_002',
    threadType: 'comment',
    tensionPoint: 'Sample size of 45 participants may limit generalizability of findings',
    keywords: ['sample size', 'methodology', 'generalizability'],
    anchor: {
      sectionId: 'section_2',
      startOffset: 0,
      endOffset: 80,
      snippetText: 'We recruited 45 participants from undergraduate courses across three disciplines',
    },
    participants: ['critical'],
    messages: [
      {
        messageId: 'msg_005',
        threadId: 'thread_002',
        author: 'critical',
        content: "45 participants across three disciplines means roughly 15 students per field. While the authors acknowledge this as a limitation, it's worth noting that disciplinary differences in reading practices could be significant. Can we really draw conclusions about 'undergraduate reading' when each discipline has such different textual traditions and expectations?",
        references: [],
        timestamp: '2024-01-15T10:35:00Z',
      },
    ],
    createdAt: '2024-01-15T10:35:00Z',
    updatedAt: '2024-01-15T10:35:00Z',
  },
  {
    threadId: 'thread_003',
    documentId: 'doc_001',
    seedId: 'seed_003',
    threadType: 'discussion',
    discussionType: 'deepening',
    tensionPoint: 'The finding that only 23% of students question claims raises questions about academic culture',
    keywords: ['authority', 'academic culture', 'student identity'],
    anchor: {
      sectionId: 'section_3',
      startOffset: 414,
      endOffset: 506,
      snippetText: 'Only 23% of students spontaneously questioned the claims or evidence presented in the texts.',
    },
    participants: ['critical', 'aesthetic'],
    messages: [
      {
        messageId: 'msg_006',
        threadId: 'thread_003',
        author: 'critical',
        content: "The quote 'Who am I to question the expert?' is telling. This isn't just about reading skills - it's about power dynamics in academia. Are we teaching students to be critical thinkers, or to defer to authority? The 23% figure might actually represent students who feel they have permission to challenge texts.",
        references: [],
        timestamp: '2024-01-15T10:40:00Z',
      },
      {
        messageId: 'msg_007',
        threadId: 'thread_003',
        author: 'aesthetic',
        content: "I wonder how this varies by student background. The paper mentions first-generation students in the sample but doesn't break down the results by this variable. Students from families where academic discourse is familiar might feel more entitled to question texts. This could be about cultural capital as much as skill.",
        references: [],
        timestamp: '2024-01-15T10:40:15Z',
      },
      {
        messageId: 'msg_008',
        threadId: 'thread_003',
        author: 'critical',
        content: "Exactly. And the proposed 'interventions' might not address this underlying issue. Teaching critical reading strategies could help, but if students still feel like imposters in academic spaces, will they actually use those strategies? The paper seems to treat this as a technical problem when it might be more fundamentally social.",
        references: [],
        timestamp: '2024-01-15T10:40:30Z',
      },
    ],
    createdAt: '2024-01-15T10:40:00Z',
    updatedAt: '2024-01-15T10:40:30Z',
  },
  {
    threadId: 'thread_004',
    documentId: 'doc_001',
    seedId: 'seed_004',
    threadType: 'comment',
    tensionPoint: 'Connection between reading and personal experience deserves more attention',
    keywords: ['personal connection', 'engagement', 'meaning-making'],
    anchor: {
      sectionId: 'section_3',
      startOffset: 703,
      endOffset: 781,
      snippetText: 'Students rarely connected reading to their own experiences or prior knowledge.',
    },
    participants: ['aesthetic'],
    messages: [
      {
        messageId: 'msg_009',
        threadId: 'thread_004',
        author: 'aesthetic',
        content: "This finding seems important but underexplored. When reading becomes personal - when we see ourselves in the text or connect it to our lives - that's when real engagement happens. I wonder if the 'disconnected reading' is partly because academic texts are written in a way that discourages personal connection. The impersonal academic voice might itself be a barrier to the kind of reading the authors want to promote.",
        references: [],
        timestamp: '2024-01-15T10:45:00Z',
      },
    ],
    createdAt: '2024-01-15T10:45:00Z',
    updatedAt: '2024-01-15T10:45:00Z',
  },
  {
    threadId: 'thread_005',
    documentId: 'doc_001',
    seedId: 'seed_005',
    threadType: 'discussion',
    discussionType: 'connecting',
    tensionPoint: 'The mention of AI-assisted tools opens interesting possibilities',
    keywords: ['AI', 'technology', 'future research'],
    anchor: {
      sectionId: 'section_4',
      startOffset: 680,
      endOffset: 825,
      snippetText: 'the use of AI-assisted tools to scaffold critical analysis',
    },
    participants: ['instrumental', 'aesthetic'],
    messages: [
      {
        messageId: 'msg_010',
        threadId: 'thread_005',
        author: 'instrumental',
        content: "The brief mention of AI tools at the end is interesting. What would AI-assisted critical reading look like? Perhaps tools that prompt students with questions, highlight assumptions, or suggest connections to other texts. This could be a practical application of the research.",
        references: [],
        timestamp: '2024-01-15T10:50:00Z',
      },
      {
        messageId: 'msg_011',
        threadId: 'thread_005',
        author: 'aesthetic',
        content: "I can imagine a tool that offers different perspectives on a text - exactly like what we're doing here! Having multiple 'voices' that model different ways of engaging with reading could show students that there's not just one right way to be critical. Though there's also a risk that it could become another thing students just accept without thinking.",
        references: [],
        timestamp: '2024-01-15T10:50:15Z',
      },
      {
        messageId: 'msg_012',
        threadId: 'thread_005',
        author: 'instrumental',
        content: "That's a great point about multiple perspectives. The tool could scaffold the transition from guided questioning to independent critical thinking. The key would be fading support over time so students internalize the strategies rather than depending on the AI.",
        references: [],
        timestamp: '2024-01-15T10:50:30Z',
      },
    ],
    createdAt: '2024-01-15T10:50:00Z',
    updatedAt: '2024-01-15T10:50:30Z',
  },
];

export const mockDocument = {
  documentId: 'doc_001',
  userId: 'user_001',
  title: 'Critical Reading Challenges in Undergraduate Education',
  originalPdfUrl: '',
  parsedContent: {
    sections: mockSections,
  },
  threads: mockThreads.map((t) => t.threadId),
  uploadedAt: '2024-01-15T10:00:00Z',
  lastAccessedAt: '2024-01-15T10:50:00Z',
};
