---
document_id: raise-agrifood-knowledge
version: "0.2"
status: ai_draft
publication_scope: pilot
production_eligible: false
source_doc_sha256: 3C0BAF8145E4A2E287BA5783F8AB26A7CEAE1C5340322C1EE065887CC9B75B0E
generated_at: 2026-08-11T00:00:00+00:00
languages: [en, ar]
scope: [Akkar, rural Lebanon]
default_review_status: ai_draft
default_translation_status: machine_draft
translation_method: local_repository_ai_draft
default_retrieval_enabled: true
ontology_version: raise-agrifood-ontology-v0.2.0
---

# RAISE Agrifood Knowledge Draft

> Pilot draft: English is the authoritative draft source. Arabic was drafted locally in the repository without an external translation service. Neither language is production-approved; high-risk details remain limited or referral-only until expert review.

## Akkar context and limits on transferring advice / سياق عكار وحدود نقل الإرشادات

```yaml
{
  "claim_ids": [
    "claim:kb-scope-local-context:guidance",
    "claim:kb-scope-local-context:decision",
    "claim:kb-scope-local-context:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "3akkar"
        }
      ],
      "id": "akkar",
      "label_ar": "عكار",
      "label_en": "Akkar",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "akkar_plain",
      "label_ar": "سهل عكار الزراعي",
      "label_en": "Akkar agricultural plain",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "akkar_uplands",
      "label_ar": "مرتفعات عكار ومدرجاتها",
      "label_en": "Akkar uplands and terraces",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "rural_lebanon",
      "label_ar": "لبنان الريفي",
      "label_en": "rural Lebanon",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "site_assessment",
      "label_ar": "تقييم الموقع",
      "label_en": "site assessment",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "water_reliability",
      "label_ar": "موثوقية مصدر المياه",
      "label_en": "water-source reliability",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "frost",
      "label_ar": "التعرض للصقيع",
      "label_en": "frost exposure",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "moa_lebanon",
      "label_ar": "وزارة الزراعة اللبنانية",
      "label_en": "Lebanon Ministry of Agriculture",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "extension_service",
      "label_ar": "خدمة الإرشاد الزراعي",
      "label_en": "agricultural extension service",
      "type": "service"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-decision-rules",
      "type": "requires_context"
    }
  ],
  "id": "kb-scope-local-context",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "3akkar"
        }
      ],
      "id": "akkar",
      "label_ar": "عكار",
      "label_en": "Akkar",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "akkar_plain",
      "label_ar": "سهل عكار الزراعي",
      "label_en": "Akkar agricultural plain",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "akkar_uplands",
      "label_ar": "مرتفعات عكار ومدرجاتها",
      "label_en": "Akkar uplands and terraces",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "rural_lebanon",
      "label_ar": "لبنان الريفي",
      "label_en": "rural Lebanon",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "site_assessment",
      "label_ar": "تقييم الموقع",
      "label_en": "site assessment",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "water_reliability",
      "label_ar": "موثوقية مصدر المياه",
      "label_en": "water-source reliability",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "frost",
      "label_ar": "التعرض للصقيع",
      "label_en": "frost exposure",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "moa_lebanon",
      "label_ar": "وزارة الزراعة اللبنانية",
      "label_en": "Lebanon Ministry of Agriculture",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "extension_service",
      "label_ar": "خدمة الإرشاد الزراعي",
      "label_en": "agricultural extension service",
      "type": "service"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "akkar",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "site_assessment",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "akkar_plain",
      "polarity": "positive",
      "qualifiers": {
        "context": "terrain"
      },
      "risk": "medium",
      "subject": "site_assessment",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "akkar_uplands",
      "polarity": "positive",
      "qualifiers": {
        "context": "altitude_and_slope"
      },
      "risk": "medium",
      "subject": "site_assessment",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "water_reliability",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "site_assessment",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "frost",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "crop_calendar",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "buyer",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "crop_calendar",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "rural_lebanon",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "professional_referral",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "moa_lebanon",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "extension_service",
      "type": "related_to"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [
    "ESDU-ABOUT-2026",
    "FAO-LEBANON-RESILIENT-LIVELIHOODS",
    "MOA-AKKAR-2026",
    "MOA-AKKAR-GREENHOUSE-2026",
    "MOA-LEBANON-NAS-2020-2025",
    "UNDP-LEBANON-NAP-2025"
  ],
  "supersedes_legacy_items": [
    "AKKAR-PROFILE-001",
    "AKKAR-SECTOR-002",
    "FARMER-QUESTION-018"
  ],
  "title_ar": "سياق عكار وحدود نقل الإرشادات",
  "title_en": "Akkar context and limits on transferring advice",
  "topics": [
    "Akkar",
    "local context",
    "applicability"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Advice for Akkar must distinguish the relatively flat agricultural plain from upland and terraced areas. Farm decisions vary with altitude, slope, soil depth, water access, frost exposure, market distance, and whether a household combines crops with livestock. A crop or calendar recommendation should therefore ask for the farmer's locality, approximate altitude or terrain, water source, production system, and intended market before becoming specific. The Ministry of Agriculture described Akkar in April 2026 as one of Lebanon's important agricultural baskets, with large potato and pome-fruit areas and expanding olive, citrus, and avocado production. These figures are dated context, not permanent production targets.

In April 2026, the Lebanese Ministry of Agriculture reported about 20,000 dunams planted with potatoes in Akkar, with roughly 70,000 tonnes for local consumption and 7,000 tonnes for processing. It also reported about 25,000 dunams of pome fruit with production near 17,000 tonnes, alongside expansion in olives, citrus, and avocado. A March 2026 ministry field visit also highlighted greenhouse tomato and cucumber farms and potato fields. Use these dated figures to prioritize knowledge and field questions, not to estimate an individual farm's expected yield or income.

When a question is broad, ask at most one or two short follow-ups at a time. Useful fields are locality, crop or animal, growth or production stage, field or herd scale, water source, main symptom or decision, timing, and market objective. Accept colloquial Arabic and voice, then restate the interpreted question plainly so the farmer can correct it. Offer a short answer first, followed by details and source cards. Do not make low literacy or limited connectivity a reason to withhold essential safety information.

Akkar cannot be treated as one uniform production environment. Recommendations may change with elevation, slope, soil depth, exposure, water source, salinity, frost risk, wind, access roads and proximity to markets. The chatbot should therefore request location at an appropriate resolution and the production setting before making locally sensitive recommendations.

The initial content supports general principles for rain-fed and irrigated field crops, orchards, greenhouses, small-ruminant and cattle systems, small-scale processing and value-chain questions. It does not yet contain approved crop calendars, variety lists, pest thresholds, water-quality maps, soil maps or farm-gate prices for Akkar.

Geographic data to add include geocoded service areas, elevation bands, agroclimatic zones, reliable weather stations, soil-survey coverage, irrigation schemes and water sources, laboratory access, market routes, land-use constraints and hazard exposure. Restricted farm or beneficiary data must be aggregated or permission-controlled.

The chatbot may explain general mechanisms, collect observations, compare low-risk options, cite sources and identify the right professional. It may not issue a definitive crop or animal diagnosis from limited text or an image, prescribe a veterinary medicine, invent a pesticide rate, certify food as safe, interpret law as legal advice or promise profit.

Photos can support information gathering but do not establish a diagnosis. Image quality, symptom overlap, unseen roots, environmental conditions, laboratory results and the user's description all affect interpretation. Answers should offer multiple plausible causes and specify evidence that separates them.

Current weather, market prices, regulations, service availability and program eligibility require a live verified source. If the live source is absent or stale, the correct answer is to disclose that current status cannot be confirmed and provide a verification pathway.

High-risk requests include suspected poisoning, zoonotic disease, sudden or unexplained animal deaths, foodborne illness, severe crop contamination, unsafe chemical handling and human injury. The immediate response is to stop exposure where safe, protect people and animals, preserve evidence and contact the appropriate qualified or emergency service; the chatbot must not improvise treatment.

The Lebanese National Agriculture Strategy 2020–2025 documented structural concerns including competitiveness, natural-resource sustainability, institutional service delivery, inclusion and exposure to economic and climate shocks (date-sensitive). Because the strategy period has ended, it is evidence of recent historical priorities rather than confirmation of current 2026 policy [source: MOA-LEBANON-NAS-2020-2025].

A recommendation that is technically sound can fail when inputs are unavailable, electricity is unreliable, pumps cannot maintain pressure, laboratories are distant, cold storage is absent, labor timing conflicts with other work or buyers reject the resulting product. Feasibility must therefore be part of the answer, not an afterthought.

Cooperatives and local institutions may reduce transaction costs and support aggregation, training or market access, but the chatbot must not assume capacity, governance quality, membership eligibility or active services. Those facts require current records.

Conflict and economic instability can interrupt transport, inputs, labor, electricity and services. The system should support contingency planning without giving security advice or presenting time-sensitive conditions as fixed. Sensitive information about beneficiaries, locations and assets requires permissions.

### Arabic guidance — machine draft

يجب أن تميّز الإرشادات الخاصة بعكار بين السهل الزراعي والمناطق المرتفعة أو المدرّجة. إن اختيار محصول مناسب للأرض في عكار يتغير بحسب الارتفاع والانحدار وعمق التربة وتوفّر المياه والتعرّض للصقيع وبُعد السوق، وبحسب اعتماد الأسرة على المحاصيل وحدها أو على نظام مختلط مع الثروة الحيوانية. لذلك، قبل إعطاء توصية دقيقة، ينبغي السؤال عن البلدة أو الموقع التقريبي، والارتفاع أو طبيعة الأرض، ومصدر المياه، ونظام الإنتاج، والسوق المستهدف. وصفت وزارة الزراعة عكار في نيسان 2026 بأنها من السلال الزراعية المهمة في لبنان، مع مساحات كبيرة للبطاطا والتفاحيات وتوسع في الزيتون والحمضيات والأفوكادو. هذه الأرقام تعطي سياقاً زمنياً ولا تمثل أهداف إنتاج ثابتة.

أفادت وزارة الزراعة اللبنانية في نيسان 2026 بوجود نحو 20 ألف دونم مزروعة بالبطاطا في عكار، مع إنتاج يقارب 70 ألف طن للاستهلاك المحلي و7 آلاف طن للتصنيع. كما أشارت إلى نحو 25 ألف دونم من التفاحيات بإنتاج يقارب 17 ألف طن، وإلى توسع زراعة الزيتون والحمضيات والأفوكادو. وأظهرت جولة للوزارة في آذار 2026 أهمية البيوت البلاستيكية المزروعة بالبندورة والخيار إضافة إلى حقول البطاطا. تُستخدم هذه الأرقام المؤرخة لتحديد أولويات المحتوى والأسئلة الميدانية، لا لتقدير مردود أو دخل مزرعة فردية.

عندما يكون السؤال عاماً، يُطرح سؤال أو سؤالان قصيران في كل مرة. تشمل المعلومات المفيدة البلدة أو الموقع، والمحصول أو الحيوان، ومرحلة النمو أو الإنتاج، وحجم الحقل أو القطيع، ومصدر المياه، والعرض الأساسي أو القرار المطلوب، والتوقيت، والهدف التسويقي. يجب قبول العربية المحكية والصوت، ثم إعادة صياغة السؤال كما فهمه النظام بلغة بسيطة كي يتمكن المزارع من تصحيحه. يُقدَّم جواب مختصر أولاً ثم التفاصيل وبطاقات المصادر. ولا يجوز أن يؤدي ضعف القراءة أو الاتصال إلى حجب معلومات السلامة الأساسية.

يجب ألّا تُعامل عكار كبيئة إنتاجية واحدة. ينبغي التمييز بين السهل الزراعي والمناطق المرتفعة أو المدرّجة، لأن الارتفاع والانحدار وعمق التربة ومصدر المياه والتعرّض للصقيع والرياح وبعد السوق ونظام الإنتاج تغيّر صلاحية التوصية. قبل تخصيص أي نصيحة، يُسأل المستخدم عن البلدة أو المنطقة التقريبية، وطبيعة الأرض أو الارتفاع التقريبي، والمحصول أو الحيوان ومرحلة الإنتاج، ومصدر المياه، وحجم النشاط، والسوق المقصود. تُستخدم أرقام وزارة الزراعة المنشورة في نيسان 2026 عن البطاطا والتفاحيات والزيتون والحمضيات والأفوكادو والبيوت المحمية كسياق مؤرّخ لتحديد أولويات المعرفة، لا كتوقع دائم لإنتاج مزرعة أو دخلها.

عندما يكون السؤال واسعاً، يُطرح سؤال أو سؤالان قصيران في كل مرة، وتُعاد صياغة ما فُهم بلغة واضحة ليصححه المستخدم. يجب قبول العربية المحكية والعربيزي والأخطاء الإملائية، وتقديم جواب قصير أولاً ثم التفاصيل والمصادر. ضعف القراءة أو الاتصال ليس سبباً لحذف تحذير سلامة أساسي.

يشمل نطاق المسودة مبادئ عامة للمحاصيل الحقلية البعلية والمروية، والبساتين، والبيوت المحمية، والمجترات الصغيرة والأبقار، والتصنيع الصغير، والأسواق وسلاسل القيمة. ولا تتضمن بعد روزنامات محاصيل أو أصنافاً أو عتبات آفات أو خرائط تربة ومياه أو أسعار باب المزرعة معتمدة لعكار. يلزم لاحقاً توثيق المناطق الزراعية المناخية ومحطات الطقس ومصادر الري والمختبرات وطرق الأسواق والمخاطر، مع تجميع بيانات المزارع الحساسة أو حمايتها بالصلاحيات.

يمكن للمساعد شرح الآليات العامة، وتنظيم الملاحظات، ومقارنة خيارات منخفضة المخاطر، وذكر المصادر، وتحديد الاختصاصي المناسب. ولا يجوز له تثبيت تشخيص نباتي أو حيواني من نص أو صورة محدودة، أو وصف دواء بيطري، أو اختراع جرعة مبيد، أو اعتماد غذاء آمناً، أو تقديم تفسير قانوني ملزم، أو ضمان الربح. الصورة أداة لجمع الأدلة وليست تشخيصاً؛ يجب ذكر الأسباب المحتملة وما يميّز بينها.

الطقس والأسعار والقوانين وتوافر الخدمات والبرامج معلومات حية. إذا تعذّر الوصول إلى مصدر حديث، يقال بوضوح إن الوضع الحالي غير مؤكّد ويُعطى مسار للتحقق. الاشتباه بالتسمم أو مرض مشترك أو نفوق مفاجئ أو مرض منقول بالغذاء أو تلوث شديد أو إصابة بشرية يستدعي وقف التعرّض حيث يكون ذلك آمناً، وحماية الناس والحيوانات، وحفظ الملصق أو الأدلة، والاتصال بخدمة مؤهلة أو طارئة من دون ارتجال علاج.

يجب فحص قابلية التنفيذ: توافر المدخلات والمياه والطاقة والمضخات والمختبر والتبريد والعمل والصيانة ومتطلبات المشتري ومخاطر الخسارة. لا يُفترض أن التعاونية أو المؤسسة المحلية فعّالة أو أن المستخدم مؤهل لخدماتها من دون سجل حديث. كما يجب التخطيط لانقطاع النقل والمدخلات والطاقة والخدمات من دون تقديم نصائح أمنية أو جمع مواقع وأصول دقيقة بلا ضرورة وحماية.

### Decision logic

If location, elevation or water source can materially change advice, do not give a single local recommendation until those variables are known. Never infer a user's exact location from a channel identifier.

Classify each request as low, moderate, high or critical risk. Critical risk triggers immediate escalation; high risk requires approved sources and a professional; moderate risk requires questions and limitations; low risk may receive general guidance with citations.

If a recommendation depends on a resource the user does not have, offer lower-resource alternatives or state that the option is not presently feasible.

### منطق القرار — مسودة آلية

إذا كان الموقع أو الارتفاع أو مصدر المياه أو نظام الإنتاج قد يغيّر النتيجة، لا تُعطَ توصية محلية واحدة قبل معرفتها، ولا يُستدل على موقع المستخدم من رقم القناة. صُنّف الخطر إلى منخفض أو متوسط أو عالٍ أو حرج: الحرج يُصعّد فوراً، والعالي يحتاج مصدراً معتمداً واختصاصياً، والمتوسط يحتاج أسئلة وحدوداً واضحة، والمنخفض يسمح بإرشاد عام موثّق. إذا كان الخيار يتطلب مورداً غير متاح، اعرض بديلاً أقل كلفة أو صرّح بأنه غير قابل للتنفيذ حالياً.

### Safe next action

Every locally adapted answer should state the location and production assumptions it relies on. When those are missing, return a general checklist and ask for them.

Developers should encode these boundaries as answer-policy tests. Content editors should mark sections not approved for production retrieval.

For recommendations with material cost or infrastructure needs, include a feasibility checklist covering equipment, energy, water, inputs, labor, skills, maintenance, buyer requirements and downside risk.

### الخطوة التالية الآمنة — مسودة آلية

اذكر في كل جواب محلي افتراضات المكان ونظام الإنتاج. عند نقصها، أعطِ قائمة تحقق عامة واطلب المعلومات الناقصة. سجّل حدود السلامة كاختبارات سياسة، وامنع استرجاع المقاطع غير المعتمدة للإنتاج. وعند وجود كلفة أو بنية تحتية مهمة، افحص المعدات والطاقة والمياه والمدخلات والعمل والمهارات والصيانة ومتطلبات المشتري والسيناريو السلبي.

### Avoid or escalate

Avoid exact local chemical, irrigation, disease or emergency advice based only on district-level geography.

The safest answer may be a refusal to provide a rate or diagnosis, followed by a useful evidence-collection checklist and referral.

Do not infer vulnerability, eligibility or security conditions. Avoid collecting exact asset or location data unless necessary and protected.

### ما يجب تجنبه أو تصعيده — مسودة آلية

تجنّب الجرعات الكيميائية أو جداول الري أو التشخيص أو تعليمات الطوارئ الدقيقة المبنية على جغرافيا عامة فقط. قد يكون الجواب الآمن رفض الجرعة أو التشخيص مع قائمة أدلة مفيدة وإحالة. لا تستنتج الهشاشة أو الأهلية أو الظروف الأمنية، ولا تجمع موقعاً أو أصولاً دقيقة إلا عند الضرورة وبحماية مناسبة.

### Evidence and applicability limits

Build a minimum geographic profile for each target locality with versioned sources and a named reviewer. Maps are evidence layers, not substitutes for site assessment.

Referral pathways and legal boundaries must be validated for Lebanon and kept current. No phone numbers or service hours are included in this draft.

Validate context through current surveys, service mapping and project records. Separate district-level observations from farm-level facts.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

تحتاج كل منطقة مستهدفة إلى ملف جغرافي أدنى بمصادر مؤرخة ومراجع مسؤول؛ الخريطة طبقة دليل وليست بديلاً عن كشف الموقع. يجب التحقق دورياً من الإحالات والحدود القانونية في لبنان. لا تتضمن هذه المسودة أرقام هاتف أو دوام خدمات، ويجب فصل المعلومة على مستوى القضاء عن حقيقة المزرعة.

### Claim-level sources

- [ESDU-ABOUT-2026] About ESDU — https://aub.edu.lb/fafs/esdu/Pages/About-ESDU.aspx
- [FAO-LEBANON-RESILIENT-LIVELIHOODS] Lebanon Plan of Action for Resilient Livelihoods — https://www.fao.org/fileadmin/user_upload/emergencies/docs/Lebanon%20Plan%20of%20Action%20for%20Resilient%20Livelihoods%202014-2018.pdf
- [MOA-AKKAR-2026] Akkar potato season and agricultural production overview, April 2026 — https://www.agriculture.gov.lb/Media/News/2026/%D9%88%D8%B2%D9%8A%D8%B1-%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D8%A9-%D9%86%D8%B2%D8%A7%D8%B1-%D9%87%D8%A7%D9%86%D9%8A-%D9%8A%D8%B7%D9%84%D9%82-%D9%85%D9%86-%D8%B9%D9%83%D8%A7%D8%B1-%D9%85%D9%88%D8%B3%D9%85-%D8%A7%D9%84%D8%A8%D8%B7%D8%A7%D8%B7%D8%A7-2
- [MOA-AKKAR-GREENHOUSE-2026] Ministry monitoring of greenhouse and potato production in Akkar, March 2026 — https://www.agriculture.gov.lb/Media/News/2026/%D9%88%D8%B2%D8%A7%D8%B1%D8%A9-%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D8%A9-%D8%AA%D8%B1%D8%B5%D8%AF-%D8%AA%D8%B7%D9%88%D8%B1-%D8%A7%D9%84%D8%A7%D9%86%D8%AA%D8%A7%D8%AC-%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D9%8A-%D9%81%D9%8A-%D8%B9%D9%83%D8%A7%D8%B1-%D8%B2%D9%8A
- [MOA-LEBANON-NAS-2020-2025] Lebanese Ministry of Agriculture / FAO. Lebanon National Agriculture Strategy 2020–2025. 2020. — https://faolex.fao.org/docs/pdf/leb202167E.pdf
- [UNDP-LEBANON-NAP-2025] Lebanon National Adaptation Plan 2025–2035 — https://www.undp.org/lebanon/publications/lebanon-national-adaptation-plan-nap

## Crop production decisions / قرارات إنتاج المحاصيل

```yaml
{
  "claim_ids": [
    "claim:kb-crop-production:guidance",
    "claim:kb-crop-production:decision",
    "claim:kb-crop-production:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "3akkar"
        }
      ],
      "id": "akkar",
      "label_ar": "عكار",
      "label_en": "Akkar",
      "type": "location"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "بطاطا"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "batata"
        }
      ],
      "id": "potato",
      "label_ar": "البطاطا",
      "label_en": "potato",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "orchard_crop",
      "label_ar": "محصول بستاني",
      "label_en": "orchard crop",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "olive",
      "label_ar": "الزيتون",
      "label_en": "olive",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "apple",
      "label_ar": "التفاح",
      "label_en": "apple",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "citrus",
      "label_ar": "الحمضيات",
      "label_en": "citrus",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "avocado",
      "label_ar": "الأفوكادو",
      "label_en": "avocado",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "legume",
      "label_ar": "بقوليات",
      "label_en": "legume",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "certified_seed_potato",
      "label_ar": "تقاوي بطاطا معتمدة",
      "label_en": "certified seed potato",
      "type": "variety"
    },
    {
      "aliases": [],
      "id": "market_suited_variety",
      "label_ar": "صنف ملائم للسوق",
      "label_en": "market-suited variety",
      "type": "variety"
    },
    {
      "aliases": [],
      "id": "planting",
      "label_ar": "مرحلة الزراعة",
      "label_en": "planting stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "vegetative",
      "label_ar": "مرحلة النمو الخضري",
      "label_en": "vegetative stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "flowering",
      "label_ar": "مرحلة الإزهار",
      "label_en": "flowering stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "insect_pest",
      "label_ar": "آفة حشرية",
      "label_en": "insect pest",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "crop_disease",
      "label_ar": "مرض نباتي",
      "label_en": "crop disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "site_assessment",
      "label_ar": "تقييم الموقع",
      "label_en": "site assessment",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "field_history",
      "label_ar": "مراجعة تاريخ الحقل",
      "label_en": "field history review",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "certified_seed_use",
      "label_ar": "استخدام تقاوي معتمدة",
      "label_en": "certified seed use",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "crop_rotation",
      "label_ar": "الدورة الزراعية",
      "label_en": "crop rotation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "scouting",
      "label_ar": "الكشف الحقلي",
      "label_en": "field scouting",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "IPM"
        },
        {
          "language": "arz",
          "script": "arabic",
          "text": "ادارة متكاملة"
        }
      ],
      "id": "ipm",
      "label_ar": "الإدارة المتكاملة للآفات",
      "label_en": "integrated pest management",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "record_keeping",
      "label_ar": "حفظ سجلات المزرعة",
      "label_en": "farm record keeping",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مي الري"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mayy el ray"
        }
      ],
      "id": "irrigation_water",
      "label_ar": "مياه الري",
      "label_en": "irrigation water",
      "type": "input"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "مبيد"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mabid"
        }
      ],
      "id": "pesticide",
      "label_ar": "مبيد زراعي",
      "label_en": "agricultural pesticide",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "planting_material",
      "label_ar": "مواد الإكثار الزراعي",
      "label_en": "planting material",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "water_quality",
      "label_ar": "نوعية المياه",
      "label_en": "water quality",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "planting_window",
      "label_ar": "نافذة الزراعة",
      "label_en": "planting window",
      "type": "season"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "LARI"
        },
        {
          "language": "arz",
          "script": "arabic",
          "text": "لاري"
        }
      ],
      "id": "lari",
      "label_ar": "مصلحة الأبحاث العلمية الزراعية",
      "label_en": "Lebanese Agricultural Research Institute",
      "type": "organization"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مهندس زراعي"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mhandes zira3e"
        }
      ],
      "id": "agronomist",
      "label_ar": "مهندس زراعي مؤهل",
      "label_en": "qualified agronomist",
      "type": "service"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-soil-management",
      "type": "depends_on"
    },
    {
      "target": "kb-water-irrigation",
      "type": "depends_on"
    }
  ],
  "id": "kb-crop-production",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "3akkar"
        }
      ],
      "id": "akkar",
      "label_ar": "عكار",
      "label_en": "Akkar",
      "type": "location"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "بطاطا"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "batata"
        }
      ],
      "id": "potato",
      "label_ar": "البطاطا",
      "label_en": "potato",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "orchard_crop",
      "label_ar": "محصول بستاني",
      "label_en": "orchard crop",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "olive",
      "label_ar": "الزيتون",
      "label_en": "olive",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "apple",
      "label_ar": "التفاح",
      "label_en": "apple",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "citrus",
      "label_ar": "الحمضيات",
      "label_en": "citrus",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "avocado",
      "label_ar": "الأفوكادو",
      "label_en": "avocado",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "legume",
      "label_ar": "بقوليات",
      "label_en": "legume",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "certified_seed_potato",
      "label_ar": "تقاوي بطاطا معتمدة",
      "label_en": "certified seed potato",
      "type": "variety"
    },
    {
      "aliases": [],
      "id": "market_suited_variety",
      "label_ar": "صنف ملائم للسوق",
      "label_en": "market-suited variety",
      "type": "variety"
    },
    {
      "aliases": [],
      "id": "planting",
      "label_ar": "مرحلة الزراعة",
      "label_en": "planting stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "vegetative",
      "label_ar": "مرحلة النمو الخضري",
      "label_en": "vegetative stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "flowering",
      "label_ar": "مرحلة الإزهار",
      "label_en": "flowering stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "insect_pest",
      "label_ar": "آفة حشرية",
      "label_en": "insect pest",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "crop_disease",
      "label_ar": "مرض نباتي",
      "label_en": "crop disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "site_assessment",
      "label_ar": "تقييم الموقع",
      "label_en": "site assessment",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "field_history",
      "label_ar": "مراجعة تاريخ الحقل",
      "label_en": "field history review",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "certified_seed_use",
      "label_ar": "استخدام تقاوي معتمدة",
      "label_en": "certified seed use",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "crop_rotation",
      "label_ar": "الدورة الزراعية",
      "label_en": "crop rotation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "scouting",
      "label_ar": "الكشف الحقلي",
      "label_en": "field scouting",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "IPM"
        },
        {
          "language": "arz",
          "script": "arabic",
          "text": "ادارة متكاملة"
        }
      ],
      "id": "ipm",
      "label_ar": "الإدارة المتكاملة للآفات",
      "label_en": "integrated pest management",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "record_keeping",
      "label_ar": "حفظ سجلات المزرعة",
      "label_en": "farm record keeping",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مي الري"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mayy el ray"
        }
      ],
      "id": "irrigation_water",
      "label_ar": "مياه الري",
      "label_en": "irrigation water",
      "type": "input"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "مبيد"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mabid"
        }
      ],
      "id": "pesticide",
      "label_ar": "مبيد زراعي",
      "label_en": "agricultural pesticide",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "planting_material",
      "label_ar": "مواد الإكثار الزراعي",
      "label_en": "planting material",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "water_quality",
      "label_ar": "نوعية المياه",
      "label_en": "water quality",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "planting_window",
      "label_ar": "نافذة الزراعة",
      "label_en": "planting window",
      "type": "season"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "LARI"
        },
        {
          "language": "arz",
          "script": "arabic",
          "text": "لاري"
        }
      ],
      "id": "lari",
      "label_ar": "مصلحة الأبحاث العلمية الزراعية",
      "label_en": "Lebanese Agricultural Research Institute",
      "type": "organization"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مهندس زراعي"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mhandes zira3e"
        }
      ],
      "id": "agronomist",
      "label_ar": "مهندس زراعي مؤهل",
      "label_en": "qualified agronomist",
      "type": "service"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "potato",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "field_history",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "certified_seed_potato",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "certified_seed_use",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "market_suited_variety",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "potato",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "water_quality",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "potato",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "soil_health",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "potato",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "soil_health",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "crop_rotation",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "ipm",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "scouting",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "crop_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "pesticide",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "pesticide_register",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "pesticide",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "agronomist",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "crop_disease",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "planting",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "planting_material",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "harvest_window",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "orchard_crop",
      "type": "requires_context"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [
    "MOA-AKKAR-2026",
    "UNDP-LEBANON-NAP-2025"
  ],
  "supersedes_legacy_items": [
    "ORCHARD-DECISIONS-005",
    "POTATO-DECISIONS-003"
  ],
  "title_ar": "قرارات إنتاج المحاصيل",
  "title_en": "Crop production decisions",
  "topics": [
    "crop",
    "potato",
    "orchard",
    "production stage"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Before advising on potatoes, collect: locality and field history; planting date; seed source and certification; variety and intended market; irrigation water source and quality; soil test if available; rotation history; observed symptoms; storage or processing destination; and the most recent Ministry of Agriculture or LARI alert. Avoid giving pesticide names, doses, or pre-harvest intervals from a static guide. Disease and pest recommendations must be tied to a confirmed diagnosis, a currently registered label, crop stage, and local expert guidance. For market planning, distinguish fresh local consumption from processing because quality specifications and timing can differ.

The orchard question should identify crop and variety, tree age, rootstock if known, locality and altitude, slope and frost pocket risk, flowering or fruit stage, irrigation source, soil drainage, pruning history, and symptoms. Apples and other pome fruits in higher areas face different temperature and frost conditions from citrus or avocado at lower elevations. Climate trends make old calendar rules less reliable, so use observed crop stage and current local conditions. Do not infer that a crop is suitable everywhere in Akkar merely because ministry reporting shows that it exists in the governorate.

Start with the production objective, buyer or household need, field history, climate and elevation, water quantity and quality, soil test, rotation, available labor, equipment, inputs and realistic market access. Crop selection based only on expected price is unsafe because price, quality, timing and yield can change.

Use healthy, traceable planting material suited to the production system. Nursery hygiene, labeling, irrigation discipline, pest exclusion and records reduce the chance of carrying problems into the field. Exact seed treatment, planting date and spacing must come from an approved crop profile.

Manage soil, water, nutrition and canopy as an interacting system. More fertilizer or water is not automatically better. Excesses can increase salinity, leaching, weak growth, disease risk and cost. Use soil or tissue evidence and crop stage before adjusting inputs.

Use rotations, cover crops, mulches, sanitation, resistant material where available, monitoring and integrated pest management. Glyphosate is prohibited in this knowledge base. Weed management should prioritize prevention, cultivation, hand or mechanical removal, mulching, cover crops, competitive stands and rotation; any other herbicide discussion requires Lebanese legality, label verification and expert approval.

Crop profile template: scientific and local names; intended market; suitable zones; planting material; site and soil needs; calendar by elevation; establishment; spacing; irrigation; nutrition; monitoring; key pests and diseases; non-chemical prevention; harvest maturity; post-harvest; expected ranges with assumptions; records; sources; local validation; expert approval.

### Arabic guidance — machine draft

قبل تقديم إرشاد حول البطاطا، يجب جمع المعلومات الآتية: موقع الحقل وتاريخه الزراعي، تاريخ الزراعة، مصدر التقاوي وشهادتها، الصنف والسوق المستهدف، مصدر مياه الري ونوعيتها، تحليل التربة إن وُجد، الدورة الزراعية، الأعراض المشاهدة، وجهة التخزين أو التصنيع، وآخر تنبيه صادر عن وزارة الزراعة أو مصلحة الأبحاث العلمية الزراعية. لا يجوز إعطاء أسماء مبيدات أو جرعات أو فترات أمان اعتماداً على دليل ثابت. يجب ربط مكافحة الآفات والأمراض بتشخيص مؤكد وبطاقة مبيد مسجّل حالياً ومرحلة نمو المحصول وإرشاد خبير محلي. وفي التخطيط التسويقي، يجب التمييز بين سوق الاستهلاك الطازج وسوق التصنيع لاختلاف المواصفات والتوقيت.

يجب أن يحدد سؤال البساتين المحصول والصنف، وعمر الأشجار، والأصل إن كان معروفاً، والبلدة والارتفاع، والانحدار وخطر تجمع الصقيع، ومرحلة الإزهار أو نمو الثمار، ومصدر الري، وصرف التربة، وتاريخ التقليم، والأعراض. تختلف ظروف الحرارة والصقيع التي تواجه التفاحيات في المناطق المرتفعة عن ظروف الحمضيات أو الأفوكادو في الارتفاعات المنخفضة. ومع تغير المناخ تصبح الروزنامة التقليدية أقل موثوقية، لذا يجب الاعتماد على مرحلة نمو النبات والظروف المحلية الحالية. ولا يعني ورود محصول في تقارير المحافظة أنه مناسب لكل مناطق عكار.

تبدأ قرارات المحاصيل بهدف الإنتاج والسوق أو حاجة الأسرة، وتاريخ الحقل، والارتفاع والمناخ، وكمية المياه ونوعيتها، وفحص التربة، والدورة الزراعية، والعمل والمعدات والمدخلات المتاحة. لا يكفي السعر المتوقع لاختيار محصول لأن السعر والجودة والتوقيت والمحصول القابل للبيع قد تتغير.

في البطاطا تُجمع معلومات الموقع وتاريخ الحقل وموعد الزراعة ومصدر التقاوي وشهادتها والصنف والسوق ومياه الري وفحص التربة والدورة والأعراض ووجهة التخزين أو التصنيع وأحدث تنبيه رسمي. وفي البساتين يُحدّد المحصول والصنف وعمر الشجرة والأصل إن عُرف والارتفاع والانحدار وخطر جيوب الصقيع والمرحلة ومصدر الري والصرف والتقليم والأعراض. وجود محصول في عكار لا يعني ملاءمته لكل موقع، كما أن مرحلة النبات والظروف الحالية أهم من قاعدة تقويم قديمة.

استخدم مواد إكثار سليمة قابلة للتتبع ومناسبة للنظام. النظافة في المشتل، والبطاقات، وضبط الري، ومنع الآفات، والسجلات تقلل نقل المشكلات. يجب أن تأتي مواعيد الزراعة والمسافات ومعاملة البذور من ملف محصول معتمد.

تُدار التربة والمياه والتغذية والمجموع الخضري كنظام مترابط؛ زيادة الماء أو السماد ليست أفضل تلقائياً وقد تزيد الملوحة والغسل والنمو الضعيف والمرض والكلفة. استند إلى تحليل التربة أو الأنسجة ومرحلة المحصول. استخدم الدورة ومحاصيل التغطية والملش والنظافة والمقاومة والرصد والإدارة المتكاملة للآفات.

سياسة RAISE تمنع تقديم توصيات الغليفوسات. تُفضّل الوقاية والعزيق والإزالة اليدوية أو الميكانيكية والملش ومحاصيل التغطية والتنافس والدورة. أي مبيد أعشاب آخر يحتاج تحققاً حديثاً من قانونيته وملصقه في لبنان ومراجعة خبير.

يتضمن ملف المحصول: الأسماء العلمية والمحلية، السوق، المناطق المناسبة، مادة الإكثار، التربة والموقع، تقويماً حسب الارتفاع، التأسيس والمسافات والري والتغذية والرصد والآفات والأمراض والوقاية غير الكيميائية والنضج وما بعد الحصاد والنطاقات المتوقعة مع افتراضاتها والسجلات والمصادر والتحقق المحلي والاعتماد.

### Decision logic

Do not give exact production inputs until crop, variety, growth stage, area, soil and water evidence, production system and legal constraints are known.

### منطق القرار — مسودة آلية

لا تُعطَ كميات مدخلات دقيقة قبل معرفة المحصول والصنف والمرحلة والمساحة والتربة والمياه ونظام الإنتاج والقيود القانونية. يجب ربط أي قرار مكافحة بتشخيص مؤكد وملصق مسجل وحديث ومرحلة المحصول وإرشاد محلي مؤهل.

### Safe next action

Create a season plan and field record before planting. Record inputs, dates, weather, irrigation, observations, labor, harvest quantity, quality and buyer outcome.

### الخطوة التالية الآمنة — مسودة آلية

أنشئ خطة موسم وسجل حقل قبل الزراعة، وسجّل المدخلات والتواريخ والطقس والري والملاحظات والعمل وكمية الحصاد ودرجته ورفضه ونتيجة البيع.

### Avoid or escalate

No pesticide rates or universal fertilizer schedules. Protect workers, pollinators, water and food; labels and Lebanese rules take precedence.

### ما يجب تجنبه أو تصعيده — مسودة آلية

لا تقدّم جرعة مبيد أو برنامج تسميد موحداً. احمِ العمال والملقحات والمياه والغذاء؛ ويتقدم الملصق الحالي والقواعد اللبنانية على أي نص ثابت.

### Evidence and applicability limits

Apply only within the stated geography, production system, season, and evidence limits.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

تطبق الإرشادات فقط ضمن المكان ونظام الإنتاج والموسم وحدود الأدلة المذكورة. تحتاج المواعيد والأصناف والعتبات والجرعات والنطاقات المحلية إلى ملفات محاصيل معتمدة ومراجعة ميدانية.

### Claim-level sources

- [MOA-AKKAR-2026] Akkar potato season and agricultural production overview, April 2026 — https://www.agriculture.gov.lb/Media/News/2026/%D9%88%D8%B2%D9%8A%D8%B1-%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D8%A9-%D9%86%D8%B2%D8%A7%D8%B1-%D9%87%D8%A7%D9%86%D9%8A-%D9%8A%D8%B7%D9%84%D9%82-%D9%85%D9%86-%D8%B9%D9%83%D8%A7%D8%B1-%D9%85%D9%88%D8%B3%D9%85-%D8%A7%D9%84%D8%A8%D8%B7%D8%A7%D8%B7%D8%A7-2
- [UNDP-LEBANON-NAP-2025] Lebanon National Adaptation Plan 2025–2035 — https://www.undp.org/lebanon/publications/lebanon-national-adaptation-plan-nap

## Livestock and mixed-farm decisions / قرارات الثروة الحيوانية والمزارع المختلطة

```yaml
{
  "claim_ids": [
    "claim:kb-livestock:guidance",
    "claim:kb-livestock:decision",
    "claim:kb-livestock:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [],
      "id": "cattle",
      "label_ar": "الأبقار",
      "label_en": "cattle",
      "type": "animal"
    },
    {
      "aliases": [],
      "id": "sheep",
      "label_ar": "الأغنام",
      "label_en": "sheep",
      "type": "animal"
    },
    {
      "aliases": [],
      "id": "goat",
      "label_ar": "الماعز",
      "label_en": "goat",
      "type": "animal"
    },
    {
      "aliases": [],
      "id": "poultry",
      "label_ar": "الدواجن",
      "label_en": "poultry",
      "type": "animal"
    },
    {
      "aliases": [],
      "id": "young_animal",
      "label_ar": "مرحلة الحيوان الصغير",
      "label_en": "young-animal stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "lactation",
      "label_ar": "مرحلة الإدرار",
      "label_en": "lactation stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "diarrhea",
      "label_ar": "إسهال الحيوان",
      "label_en": "animal diarrhea",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "respiratory_distress",
      "label_ar": "ضيق التنفس",
      "label_en": "respiratory distress",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "lameness",
      "label_ar": "العرج",
      "label_en": "lameness",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "sudden_mortality",
      "label_ar": "نفوق مفاجئ",
      "label_en": "sudden mortality",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "rodent",
      "label_ar": "قارض",
      "label_en": "rodent",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "animal_disease",
      "label_ar": "مرض حيواني",
      "label_en": "animal disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "zoonotic_disease",
      "label_ar": "مرض حيواني المنشأ",
      "label_en": "zoonotic disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "sanitation",
      "label_ar": "النظافة الزراعية",
      "label_en": "farm sanitation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "biosecurity",
      "label_ar": "الأمن الحيوي",
      "label_en": "farm biosecurity",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "ventilation",
      "label_ar": "تهوية الدفيئة",
      "label_en": "greenhouse ventilation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "shade_management",
      "label_ar": "إدارة التظليل",
      "label_en": "shade management",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "record_keeping",
      "label_ar": "حفظ سجلات المزرعة",
      "label_en": "farm record keeping",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "hygiene",
      "label_ar": "ممارسات النظافة الجيدة",
      "label_en": "good hygiene practice",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "isolation",
      "label_ar": "عزل الخطر",
      "label_en": "risk isolation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "veterinary_medicine",
      "label_ar": "دواء بيطري",
      "label_en": "veterinary medicine",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "antimicrobial",
      "label_ar": "مضاد ميكروبي",
      "label_en": "antimicrobial",
      "type": "input"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "دكتور بيطري"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "doctor baytari"
        }
      ],
      "id": "veterinarian",
      "label_ar": "طبيب بيطري",
      "label_en": "veterinarian",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "withdrawal_period",
      "label_ar": "فترة سحب الدواء البيطري",
      "label_en": "veterinary withdrawal period",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "zoonotic_exposure",
      "label_ar": "تعرض لمرض حيواني المنشأ",
      "label_en": "zoonotic exposure",
      "type": "risk"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-referrals",
      "type": "escalates_to"
    }
  ],
  "id": "kb-livestock",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [],
      "id": "cattle",
      "label_ar": "الأبقار",
      "label_en": "cattle",
      "type": "animal"
    },
    {
      "aliases": [],
      "id": "sheep",
      "label_ar": "الأغنام",
      "label_en": "sheep",
      "type": "animal"
    },
    {
      "aliases": [],
      "id": "goat",
      "label_ar": "الماعز",
      "label_en": "goat",
      "type": "animal"
    },
    {
      "aliases": [],
      "id": "poultry",
      "label_ar": "الدواجن",
      "label_en": "poultry",
      "type": "animal"
    },
    {
      "aliases": [],
      "id": "young_animal",
      "label_ar": "مرحلة الحيوان الصغير",
      "label_en": "young-animal stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "lactation",
      "label_ar": "مرحلة الإدرار",
      "label_en": "lactation stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "diarrhea",
      "label_ar": "إسهال الحيوان",
      "label_en": "animal diarrhea",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "respiratory_distress",
      "label_ar": "ضيق التنفس",
      "label_en": "respiratory distress",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "lameness",
      "label_ar": "العرج",
      "label_en": "lameness",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "sudden_mortality",
      "label_ar": "نفوق مفاجئ",
      "label_en": "sudden mortality",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "rodent",
      "label_ar": "قارض",
      "label_en": "rodent",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "animal_disease",
      "label_ar": "مرض حيواني",
      "label_en": "animal disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "zoonotic_disease",
      "label_ar": "مرض حيواني المنشأ",
      "label_en": "zoonotic disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "sanitation",
      "label_ar": "النظافة الزراعية",
      "label_en": "farm sanitation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "biosecurity",
      "label_ar": "الأمن الحيوي",
      "label_en": "farm biosecurity",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "ventilation",
      "label_ar": "تهوية الدفيئة",
      "label_en": "greenhouse ventilation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "shade_management",
      "label_ar": "إدارة التظليل",
      "label_en": "shade management",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "record_keeping",
      "label_ar": "حفظ سجلات المزرعة",
      "label_en": "farm record keeping",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "hygiene",
      "label_ar": "ممارسات النظافة الجيدة",
      "label_en": "good hygiene practice",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "isolation",
      "label_ar": "عزل الخطر",
      "label_en": "risk isolation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "veterinary_medicine",
      "label_ar": "دواء بيطري",
      "label_en": "veterinary medicine",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "antimicrobial",
      "label_ar": "مضاد ميكروبي",
      "label_en": "antimicrobial",
      "type": "input"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "دكتور بيطري"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "doctor baytari"
        }
      ],
      "id": "veterinarian",
      "label_ar": "طبيب بيطري",
      "label_en": "veterinarian",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "withdrawal_period",
      "label_ar": "فترة سحب الدواء البيطري",
      "label_en": "veterinary withdrawal period",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "zoonotic_exposure",
      "label_ar": "تعرض لمرض حيواني المنشأ",
      "label_en": "zoonotic exposure",
      "type": "risk"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "cattle",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "biosecurity",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "sheep",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "biosecurity",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "goat",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "biosecurity",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "poultry",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "biosecurity",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "zoonotic_exposure",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "biosecurity",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "animal_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "isolation",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "veterinarian",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "critical",
      "subject": "sudden_mortality",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "veterinarian",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "critical",
      "subject": "respiratory_distress",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "young_animal",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "diarrhea",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "animal_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "veterinary_medicine",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "withdrawal_period",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "veterinary_medicine",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "veterinarian",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "antimicrobial",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "biosecurity",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "hygiene",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "poultry",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "ventilation",
      "type": "applies_to"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "high",
  "source_ids": [
    "ESDU-AKKAR-VALUECHAINS",
    "ESDU-CLIMAT-AKKAR",
    "FAO-LEBANON-RESILIENT-LIVELIHOODS",
    "WOAH-ANTIMICROBIAL-USE-2024"
  ],
  "supersedes_legacy_items": [
    "LIVESTOCK-SYSTEMS-008"
  ],
  "title_ar": "قرارات الثروة الحيوانية والمزارع المختلطة",
  "title_en": "Livestock and mixed-farm decisions",
  "topics": [
    "animal",
    "livestock",
    "mixed farm"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Good animal production begins with species-appropriate housing, clean water, balanced feed, ventilation, shade, stocking density, hygiene, observation and records. Requirements vary by species, age, physiological stage, production goal and environment; this draft does not prescribe rations or housing dimensions.

Biosecurity combines controlled animal entry, isolation when appropriate, cleaning and disinfection, visitor and equipment control, pest management, carcass handling, vaccination plans under veterinary oversight and rapid reporting of unusual illness. A checklist must be adapted to the farm and disease risks.

Reduced appetite, changes in behavior, breathing difficulty, diarrhea, neurological signs, lameness, reproductive problems, reduced production and abnormal mortality are signals to collect evidence and seek veterinary assessment. Sudden or multiple deaths, suspected zoonosis or severe respiratory or neurological signs require urgent escalation.

Antimicrobials should be used responsibly under authorized veterinary oversight, with diagnosis, product authorization, records and withdrawal periods. WOAH emphasizes husbandry, hygiene, biosecurity, vaccination, laboratory support and alternatives that reduce the need for antimicrobials [source: WOAH-ANTIMICROBIAL-USE-2024]. The chatbot must not select a drug or dose.

Heat risk depends on temperature, humidity, air movement, solar load, housing, water and animal factors. Safe general measures include reliable clean water, shade, ventilation, reduced handling during peak heat and close observation; species-specific thresholds require veterinary and local review.

### Arabic guidance — machine draft

يبدأ الإنتاج الحيواني الجيد بمسكن مناسب للنوع، ومياه نظيفة، وعلف متوازن، وتهوية وظل وكثافة مناسبة ونظافة ومراقبة وسجلات. تختلف المتطلبات حسب النوع والعمر والمرحلة الفيزيولوجية والهدف والبيئة، لذلك لا تحدد هذه المسودة عليقة أو أبعاد مسكن.

تشمل الحماية الحيوية ضبط إدخال الحيوانات، والعزل عند الحاجة، والتنظيف والتطهير، وضبط الزوار والمعدات والآفات، والتعامل الآمن مع الجثث، وخطة تلقيح بإشراف بيطري، والإبلاغ السريع عن المرض غير المعتاد. يُكيّف كل إجراء مع المزرعة ومخاطر المرض.

نقص الشهية أو تغير السلوك أو صعوبة التنفس أو الإسهال أو العلامات العصبية أو العرج أو مشكلات التكاثر أو انخفاض الإنتاج أو النفوق غير الطبيعي تستلزم جمع الأدلة وتقييماً بيطرياً. النفوق المفاجئ أو المتعدد، أو الاشتباه بمرض ينتقل للإنسان، أو العلامات التنفسية أو العصبية الشديدة حالة عاجلة.

تُستخدم مضادات الميكروبات بمسؤولية وتحت إشراف بيطري مخوّل، مع تشخيص ومنتج مرخص وسجل وفترة سحب. التربية والنظافة والحماية الحيوية والتلقيح والمختبر والبدائل تقلل الحاجة إليها [source: WOAH-ANTIMICROBIAL-USE-2024]، ولا يختار المساعد دواء أو جرعة.

يتأثر الإجهاد الحراري بالحرارة والرطوبة وحركة الهواء والشمس والمسكن والمياه وحالة الحيوان. إجراءات عامة منخفضة المخاطر هي توفير ماء نظيف موثوق وظل وتهوية، وتقليل المناولة وقت ذروة الحر، والمراقبة. أما العتبات الخاصة بالنوع فتحتاج طبيباً بيطرياً ومراجعة محلية.

### Decision logic

If severe signs, rapid spread, sudden mortality or possible human exposure is present, isolate risk where safe and contact a veterinarian or authority; do not wait for chatbot troubleshooting.

### منطق القرار — مسودة آلية

عند وجود علامات شديدة أو انتشار سريع أو نفوق مفاجئ أو تعرض محتمل للإنسان، اعزل الخطر إن أمكن بأمان واتصل بطبيب بيطري أو سلطة مختصة؛ لا تنتظر استكمال استكشاف المساعد.

### Safe next action

Maintain daily records of feed, water, production, behavior, treatments, births, deaths and environmental problems. Use them to detect change early and support the veterinarian.

### الخطوة التالية الآمنة — مسودة آلية

احتفظ بسجل يومي للعلف والماء والإنتاج والسلوك والعلاجات والولادات والنفوق والمشكلات البيئية، واستخدم تغيراته للكشف المبكر ولمساعدة الطبيب البيطري.

### Avoid or escalate

No definitive diagnosis, medication, dose or withdrawal claim without qualified review and current product information.

### ما يجب تجنبه أو تصعيده — مسودة آلية

لا تثبّت تشخيصاً ولا دواء ولا جرعة ولا فترة سحب من دون تقييم مؤهل ومعلومات منتج حديثة.

### Evidence and applicability limits

Validate species priorities, housing practices, feed availability, laboratory routes, veterinary coverage and common Arabic terms in Akkar.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

يجب التحقق ميدانياً من الأنواع ذات الأولوية والمسكن والعلف المتاح ومسارات المختبر والتغطية البيطرية والمصطلحات العربية الشائعة في عكار.

### Claim-level sources

- [ESDU-AKKAR-VALUECHAINS] Value Chains for Improved Socioeconomic Well-being of Syrian Refugees and Lebanese Host Communities — https://www.aub.edu.lb/fafs/esdu/Pages/vcproject.aspx
- [ESDU-CLIMAT-AKKAR] ESDU/WFP climate-resilient livestock and rural livelihoods work in Akkar — https://www.aub.edu.lb/fafs/esdu/Documents/ToR_ESDU_Community%20mobilizer_WFP_Akkar%20.pdf
- [FAO-LEBANON-RESILIENT-LIVELIHOODS] Lebanon Plan of Action for Resilient Livelihoods — https://www.fao.org/fileadmin/user_upload/emergencies/docs/Lebanon%20Plan%20of%20Action%20for%20Resilient%20Livelihoods%202014-2018.pdf
- [WOAH-ANTIMICROBIAL-USE-2024] WOAH. Responsible and prudent use of antimicrobial agents in veterinary medicine, Chapter 6.10. 2024. — https://www.woah.org/fileadmin/Home/eng/Health_standards/tahc/2023/chapitre_antibio_use.pdf

## Soil observation, testing, and fertility decisions / قرارات معاينة التربة وفحصها وخصوبتها

```yaml
{
  "claim_ids": [
    "claim:kb-soil-management:guidance",
    "claim:kb-soil-management:decision",
    "claim:kb-soil-management:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [],
      "id": "legume",
      "label_ar": "بقوليات",
      "label_en": "legume",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "root_damage",
      "label_ar": "ضرر الجذور",
      "label_en": "root damage",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "field_history",
      "label_ar": "مراجعة تاريخ الحقل",
      "label_en": "field history review",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "crop_rotation",
      "label_ar": "الدورة الزراعية",
      "label_en": "crop rotation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "soil_sampling",
      "label_ar": "أخذ عينة تربة ممثلة",
      "label_en": "representative soil sampling",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "smad"
        }
      ],
      "id": "fertilizer",
      "label_ar": "سماد",
      "label_en": "fertilizer",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "manure",
      "label_ar": "روث حيواني",
      "label_en": "manure",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "compost",
      "label_ar": "سماد عضوي معالج",
      "label_en": "compost",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "soil_health",
      "label_ar": "صحة التربة",
      "label_en": "soil health",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "salinity",
      "label_ar": "ملوحة التربة",
      "label_en": "soil salinity",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "sodicity",
      "label_ar": "صودية التربة",
      "label_en": "soil sodicity",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "soil_ph",
      "label_ar": "درجة حموضة التربة",
      "label_en": "soil pH",
      "type": "soil"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "EC"
        }
      ],
      "id": "soil_ec",
      "label_ar": "التوصيل الكهربائي للتربة",
      "label_en": "soil electrical conductivity",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "compaction",
      "label_ar": "انضغاط التربة",
      "label_en": "soil compaction",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "waterlogging",
      "label_ar": "تغدق التربة",
      "label_en": "waterlogging",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "drainage",
      "label_ar": "صرف التربة",
      "label_en": "soil drainage",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "organic_matter",
      "label_ar": "المادة العضوية في التربة",
      "label_en": "soil organic matter",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "soil_water_lab",
      "label_ar": "مختبر تربة ومياه",
      "label_en": "soil and water laboratory",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "fertilizer_loss",
      "label_ar": "فقد الأسمدة",
      "label_en": "fertilizer loss",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "soil_conservation",
      "label_ar": "حفظ التربة",
      "label_en": "soil conservation",
      "type": "sustainability_impact"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-crop-production",
      "type": "supports_action"
    }
  ],
  "id": "kb-soil-management",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [],
      "id": "legume",
      "label_ar": "بقوليات",
      "label_en": "legume",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "root_damage",
      "label_ar": "ضرر الجذور",
      "label_en": "root damage",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "field_history",
      "label_ar": "مراجعة تاريخ الحقل",
      "label_en": "field history review",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "crop_rotation",
      "label_ar": "الدورة الزراعية",
      "label_en": "crop rotation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "soil_sampling",
      "label_ar": "أخذ عينة تربة ممثلة",
      "label_en": "representative soil sampling",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "smad"
        }
      ],
      "id": "fertilizer",
      "label_ar": "سماد",
      "label_en": "fertilizer",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "manure",
      "label_ar": "روث حيواني",
      "label_en": "manure",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "compost",
      "label_ar": "سماد عضوي معالج",
      "label_en": "compost",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "soil_health",
      "label_ar": "صحة التربة",
      "label_en": "soil health",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "salinity",
      "label_ar": "ملوحة التربة",
      "label_en": "soil salinity",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "sodicity",
      "label_ar": "صودية التربة",
      "label_en": "soil sodicity",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "soil_ph",
      "label_ar": "درجة حموضة التربة",
      "label_en": "soil pH",
      "type": "soil"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "EC"
        }
      ],
      "id": "soil_ec",
      "label_ar": "التوصيل الكهربائي للتربة",
      "label_en": "soil electrical conductivity",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "compaction",
      "label_ar": "انضغاط التربة",
      "label_en": "soil compaction",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "waterlogging",
      "label_ar": "تغدق التربة",
      "label_en": "waterlogging",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "drainage",
      "label_ar": "صرف التربة",
      "label_en": "soil drainage",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "organic_matter",
      "label_ar": "المادة العضوية في التربة",
      "label_en": "soil organic matter",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "soil_water_lab",
      "label_ar": "مختبر تربة ومياه",
      "label_en": "soil and water laboratory",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "fertilizer_loss",
      "label_ar": "فقد الأسمدة",
      "label_en": "fertilizer loss",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "soil_conservation",
      "label_ar": "حفظ التربة",
      "label_en": "soil conservation",
      "type": "sustainability_impact"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "soil_health",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "soil_sampling",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "field_history",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "soil_sampling",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "soil_ph",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "fertilizer",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "soil_ec",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "fertilizer",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "organic_matter",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "fertilizer",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "stunting",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "salinity",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "root_damage",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "waterlogging",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "root_damage",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "compaction",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "waterlogging",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "drainage",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "soil_health",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "compost",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "food_contamination",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "manure",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "soil_conservation",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "crop_rotation",
      "type": "supports_action"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [
    "ESDU-CLIMAT-AKKAR",
    "ESDU-FARMING-FOR-ALL",
    "FAO-SOIL-TESTING-2019",
    "FAO-WATER-QUALITY-1985"
  ],
  "supersedes_legacy_items": [
    "SOIL-FERTILITY-007"
  ],
  "title_ar": "قرارات معاينة التربة وفحصها وخصوبتها",
  "title_en": "Soil observation, testing, and fertility decisions",
  "topics": [
    "soil",
    "fertility",
    "soil testing"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Soil supports roots, water storage, aeration, nutrient cycling and biological activity. A visible symptom rarely identifies a single soil problem. Field history, profile observations, root condition, irrigation, drainage and laboratory evidence should be combined.

Representative sampling is more important than collecting many convenient samples. Divide unlike areas, avoid unusual spots unless sampled separately, use clean equipment, follow a documented depth and pattern, label samples and record recent fertilizer, manure or irrigation events. The laboratory's instructions take precedence.

pH, electrical conductivity, organic matter, texture and nutrient results are method-dependent and context-dependent. A number without units, extraction method, sample depth and crop context should not drive an amendment. Salinity management requires attention to water quality, drainage, salt source and monitoring over time [sources: FAO-SOIL-TESTING-2019, FAO-WATER-QUALITY-1985].

Organic amendments can improve soil properties but vary in maturity, salinity, nutrient content, pathogens and contaminants. Manure and compost use requires source control, safe handling and crop/food-safety review. Exact application rates need analysis and a nutrient plan.

Soil diagnostic pathway: define affected pattern; compare healthy and affected areas; inspect roots and profile; review irrigation and inputs; test soil and, where relevant, water or tissue; consider compaction, waterlogging, salinity, pH, nutrient imbalance and disease; avoid treatment until evidence separates them.

### Arabic guidance — machine draft

تدعم التربة الجذور وتخزين الماء والتهوية ودورة العناصر والنشاط الحيوي، ولا يدل العرض المرئي عادة على سبب واحد. يُجمع تاريخ الحقل ووصف مقطع التربة والجذور والري والصرف والنتائج المخبرية.

العينة الممثلة أهم من كثرة العينات السهلة. افصل المناطق المختلفة، وتجنب المواقع الشاذة إلا إذا أخذت لها عينة مستقلة، واستعمل أدوات نظيفة وعمقاً ونمطاً موثقين، وضع بطاقة وسجّل آخر تسميد أو سماد عضوي أو ري. تتقدم تعليمات المختبر.

تتوقف قراءة الحموضة والموصلية الكهربائية والمادة العضوية والقوام والعناصر على الطريقة والسياق. لا يُبنى تعديل على رقم بلا وحدة وطريقة استخلاص وعمق ومحصول. تتطلب الملوحة معرفة نوعية المياه والصرف ومصدر الملح والمتابعة عبر الزمن [sources: FAO-WATER-QUALITY-1985, FAO-SOIL-TESTING-2019].

قد تحسن الإضافات العضوية خصائص التربة لكنها تختلف في النضج والملوحة والعناصر والممرضات والملوثات. السماد البلدي والكمبوست يحتاجان ضبط المصدر والتعامل الآمن ومراجعة سلامة المحصول والغذاء؛ والكمية الدقيقة تحتاج تحليلاً وخطة عناصر.

مسار التشخيص: حدّد نمط المنطقة المتأثرة، وقارن السليم بالمتأثر، وافحص الجذور والمقطع، وراجع الري والمدخلات، وافحص التربة وربما الماء أو الأنسجة، ثم ميّز بين الانضغاط والتغدق والملوحة والحموضة واختلال العناصر والمرض قبل العلاج.

### Decision logic

If only leaf color is known, do not prescribe fertilizer. Ask for crop, stage, pattern, soil and root observations, irrigation history and test results.

### منطق القرار — مسودة آلية

إذا كانت المعلومة الوحيدة لون الورقة، فلا توصف سماداً. اسأل عن المحصول والمرحلة والنمط والتربة والجذور وتاريخ الري ونتائج الفحوص.

### Safe next action

Keep a georeferenced or field-coded soil-test history with methods, units, sampling conditions and actions taken.

### الخطوة التالية الآمنة — مسودة آلية

احتفظ بتاريخ فحوص مرتبط برمز الحقل أو موقعه، مع الطريقة والوحدات وظروف أخذ العينة والإجراء الذي اتُّخذ والنتيجة.

### Avoid or escalate

Contamination suspicion, sewage exposure or industrial history requires specialist assessment; do not declare soil safe from a basic fertility test.

### ما يجب تجنبه أو تصعيده — مسودة آلية

الاشتباه بتلوث أو مياه صرف أو نشاط صناعي سابق يحتاج اختصاصياً؛ ولا يجوز إعلان التربة آمنة اعتماداً على فحص خصوبة أساسي.

### Evidence and applicability limits

Establish approved laboratories, sampling protocols and interpretation ranges for priority crops and soils in Akkar.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

يلزم اعتماد مختبرات وبروتوكولات أخذ عينات ونطاقات تفسير للمحاصيل والترب ذات الأولوية في عكار.

### Claim-level sources

- [ESDU-CLIMAT-AKKAR] ESDU/WFP climate-resilient livestock and rural livelihoods work in Akkar — https://www.aub.edu.lb/fafs/esdu/Documents/ToR_ESDU_Community%20mobilizer_WFP_Akkar%20.pdf
- [ESDU-FARMING-FOR-ALL] Farming For All: Introduction to Sustainable Agriculture — https://www.aub.edu.lb/cec/Pages/Farming-For-All.aspx
- [FAO-SOIL-TESTING-2019] FAO. Soil testing methods manual. 2019. — https://openknowledge.fao.org/3/ca2796en/ca2796en.pdf
- [FAO-WATER-QUALITY-1985] FAO. Water quality for agriculture. 1985. — https://www.fao.org/4/t0234e/t0234e00.htm

## Water and irrigation decisions / قرارات المياه والري

```yaml
{
  "claim_ids": [
    "claim:kb-water-irrigation:guidance",
    "claim:kb-water-irrigation:decision",
    "claim:kb-water-irrigation:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "jadwalet el ray"
        }
      ],
      "id": "irrigation_scheduling",
      "label_ar": "جدولة الري",
      "label_en": "irrigation scheduling",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "drip_maintenance",
      "label_ar": "صيانة نظام التنقيط",
      "label_en": "drip-system maintenance",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مي الري"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mayy el ray"
        }
      ],
      "id": "irrigation_water",
      "label_ar": "مياه الري",
      "label_en": "irrigation water",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "drainage",
      "label_ar": "صرف التربة",
      "label_en": "soil drainage",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "water_quality",
      "label_ar": "نوعية المياه",
      "label_en": "water quality",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "water_reliability",
      "label_ar": "موثوقية مصدر المياه",
      "label_en": "water-source reliability",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "emitter_flow",
      "label_ar": "تصريف النقاط",
      "label_en": "emitter flow",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "pressure_uniformity",
      "label_ar": "تجانس ضغط الري",
      "label_en": "irrigation pressure uniformity",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "root_zone_moisture",
      "label_ar": "رطوبة منطقة الجذور",
      "label_en": "root-zone moisture",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "rainwater_harvesting",
      "label_ar": "حصاد مياه الأمطار",
      "label_en": "rainwater harvesting",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "drought",
      "label_ar": "الجفاف",
      "label_en": "drought",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "soil_water_lab",
      "label_ar": "مختبر تربة ومياه",
      "label_en": "soil and water laboratory",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "irrigation_engineer",
      "label_ar": "مهندس ري",
      "label_en": "irrigation engineer",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "water_use",
      "label_ar": "استخدام المياه",
      "label_en": "water use",
      "type": "sustainability_impact"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-climate-season",
      "type": "depends_on"
    }
  ],
  "id": "kb-water-irrigation",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "jadwalet el ray"
        }
      ],
      "id": "irrigation_scheduling",
      "label_ar": "جدولة الري",
      "label_en": "irrigation scheduling",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "drip_maintenance",
      "label_ar": "صيانة نظام التنقيط",
      "label_en": "drip-system maintenance",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مي الري"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mayy el ray"
        }
      ],
      "id": "irrigation_water",
      "label_ar": "مياه الري",
      "label_en": "irrigation water",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "drainage",
      "label_ar": "صرف التربة",
      "label_en": "soil drainage",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "water_quality",
      "label_ar": "نوعية المياه",
      "label_en": "water quality",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "water_reliability",
      "label_ar": "موثوقية مصدر المياه",
      "label_en": "water-source reliability",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "emitter_flow",
      "label_ar": "تصريف النقاط",
      "label_en": "emitter flow",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "pressure_uniformity",
      "label_ar": "تجانس ضغط الري",
      "label_en": "irrigation pressure uniformity",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "root_zone_moisture",
      "label_ar": "رطوبة منطقة الجذور",
      "label_en": "root-zone moisture",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "rainwater_harvesting",
      "label_ar": "حصاد مياه الأمطار",
      "label_en": "rainwater harvesting",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "drought",
      "label_ar": "الجفاف",
      "label_en": "drought",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "soil_water_lab",
      "label_ar": "مختبر تربة ومياه",
      "label_en": "soil and water laboratory",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "irrigation_engineer",
      "label_ar": "مهندس ري",
      "label_en": "irrigation engineer",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "water_use",
      "label_ar": "استخدام المياه",
      "label_en": "water use",
      "type": "sustainability_impact"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "emitter_flow",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "irrigation_scheduling",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "root_zone_moisture",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "irrigation_scheduling",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "water_quality",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "irrigation_scheduling",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "heat",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "irrigation_scheduling",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "pressure_uniformity",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "drip_maintenance",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "soil_health",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "drainage",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "water_reliability",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "rainwater_harvesting",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "crop_calendar",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "water_reliability",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "water_quality",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "irrigation_water",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "water_use",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "irrigation_scheduling",
      "type": "supports_action"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [
    "ESDU-CLIMAT-AKKAR",
    "FAO-CROP-EVAPOTRANSPIRATION-56-2025",
    "FAO-WATER-QUALITY-1985",
    "UNDP-IRRIGATION-AKKAR",
    "UNDP-LEBANON-NAP-2025",
    "WHO-GROWING-SAFER-PRODUCE-2012"
  ],
  "supersedes_legacy_items": [
    "WATER-IRRIGATION-006"
  ],
  "title_ar": "قرارات المياه والري",
  "title_en": "Water and irrigation decisions",
  "topics": [
    "water",
    "irrigation",
    "water quality"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Water advice must account for both farm practice and shared infrastructure. UNDP reports that irrigation is Lebanon's largest water user and that low-efficiency systems and water losses constrain production; projects in Akkar and other governorates have rehabilitated canals, constructed hill lakes, and trained communities on rainwater harvesting and water-saving devices. At farm level, begin with source reliability, water quality, delivery method, leaks, pressure uniformity, soil texture, root depth, crop stage, recent weather, and an irrigation record. Avoid a universal schedule. Promote measured application, maintenance, mulching or soil-cover practices where agronomically appropriate, and safe rainwater storage. Engineering design and water-quality interpretation require qualified local support.

Irrigation scheduling should respond to crop stage, weather demand, rooting depth, soil water-holding behavior, rainfall, system capacity and measured field conditions. FAO 56 provides a framework using reference evapotranspiration and crop coefficients; values must be selected for the local crop and conditions rather than copied blindly [source: FAO-CROP-EVAPOTRANSPIRATION-56-2025].

A water-quality result must include source, date, sampling method, units and laboratory method. Salinity, sodicity, specific ions and microbiological hazards affect different decisions. Water acceptable for one crop, soil or use may be unsuitable for another [sources: FAO-WATER-QUALITY-1985, WHO-GROWING-SAFER-PRODUCE-2012].

Uneven drip irrigation may result from pressure variation, clogged filters or emitters, leaks, poor design, elevation, inadequate pump capacity, damaged lines or inconsistent operating time. Compare pressure and discharge at representative points before changing irrigation duration.

Wilting can occur from too little water, too much water and root oxygen loss, root disease, salinity, heat, transplant shock or damaged roots. Check soil moisture and roots rather than assuming drought. Poor drainage must be addressed before adding more irrigation.

Troubleshooting trees: verify source and pump; inspect filter and leaks; measure pressure; compare emitter discharge; map affected pattern; inspect soil wetting and roots; review schedule and weather; test water where indicated; then select maintenance or agronomic action.

### Arabic guidance — machine draft

يجب أن يأخذ إرشاد المياه في الحسبان ممارسة المزرعة والبنية التحتية المشتركة معاً. تشير تقارير برنامج الأمم المتحدة الإنمائي إلى أن الري هو أكبر مستخدم للمياه في لبنان، وأن ضعف الكفاءة وفاقد المياه يحدّان من الإنتاج. وشملت المشاريع في عكار ومحافظات أخرى تأهيل الأقنية وإنشاء بحيرات جبلية والتدريب على حصاد مياه الأمطار وأدوات توفير المياه. على مستوى المزرعة، يبدأ التقييم بموثوقية المصدر ونوعية المياه وطريقة التوزيع والتسربات وانتظام الضغط وقوام التربة وعمق الجذور ومرحلة المحصول والطقس الحديث وسجل الري. لا يوجد برنامج واحد يصلح للجميع. يُشجَّع قياس كميات المياه والصيانة والتغطية أو حماية سطح التربة حين تكون مناسبة، والتخزين الآمن لمياه الأمطار. أما التصميم الهندسي وتفسير تحاليل المياه فيحتاجان إلى دعم محلي مؤهل.

تراعي نصيحة المياه ممارسة المزرعة والبنية المشتركة. ابدأ بموثوقية المصدر ونوعية الماء وطريقة التوصيل والتسرب والضغط وانتظام التصريف وقوام التربة وعمق الجذور والمرحلة والطقس والمطر وسجل الري. لا تستخدم برنامجاً موحداً. شجّع القياس والصيانة والغطاء الأرضي أو الملش حيث يلائم، والتخزين الآمن لمياه الأمطار؛ أما التصميم الهندسي وتفسير النوعية فيحتاجان دعماً محلياً مؤهلاً.

يرتبط توقيت الري بمرحلة المحصول والطلب الجوي وعمق الجذور وقدرة التربة على الاحتفاظ بالماء والمطر وطاقة الشبكة والقياس الحقلي. إطار FAO 56 للتبخر-نتح المرجعي ومعاملات المحصول يحتاج قيماً مختارة للمحصول والظروف المحلية، لا نسخاً آلياً [source: FAO-CROP-EVAPOTRANSPIRATION-56-2025].

نتيجة نوعية الماء يجب أن تذكر المصدر والتاريخ وطريقة العينة والوحدة وطريقة المختبر. الملوحة والصودية والأيونات المحددة والمخاطر الميكروبية تؤثر في قرارات مختلفة؛ الماء المناسب لمحصول أو تربة أو استعمال قد لا يناسب غيره [sources: FAO-WATER-QUALITY-1985, WHO-GROWING-SAFER-PRODUCE-2012].

عدم انتظام التنقيط قد ينتج عن تغير الضغط أو انسداد المرشح أو النقاطات أو التسرب أو سوء التصميم أو فرق الارتفاع أو ضعف المضخة أو تلف الأنابيب أو تفاوت وقت التشغيل. قارن الضغط والتصريف في نقاط ممثلة قبل زيادة المدة.

قد يكون الذبول من نقص الماء أو زيادته ونقص أكسجين الجذور، أو مرض الجذور، أو الملوحة، أو الحر، أو صدمة الشتل، أو تلف الجذور. افحص رطوبة منطقة الجذر والجذور ولا تفترض الجفاف؛ عالج الصرف قبل إضافة ماء. ابدأ استكشاف الأشجار بالمصدر والمضخة والمرشح والتسرب والضغط وتصريف النقاطات ونمط الضرر وبلل التربة والجذور والبرنامج والطقس، ثم افحص الماء عند الحاجة.

### Decision logic

Do not recommend a fixed irrigation duration without emitter flow, area, system layout, soil, crop stage and weather demand.

### منطق القرار — مسودة آلية

لا تحدد مدة ري قبل معرفة تصريف النقاطات والمساحة وتصميم الشبكة والتربة ومرحلة المحصول والطلب المناخي.

### Safe next action

Maintain records for runtime, zone, pressure, flow, filter service, rainfall, soil moisture and crop response. A water balance is more useful than memory.

### الخطوة التالية الآمنة — مسودة آلية

سجّل مدة التشغيل والمنطقة والضغط والتدفق وصيانة المرشح والمطر ورطوبة التربة واستجابة المحصول. ميزان الماء أدق من الذاكرة.

### Avoid or escalate

Water used near harvest or in food processing requires a risk-based hygiene assessment. Electrical pump faults and contaminated sources require qualified help.

### ما يجب تجنبه أو تصعيده — مسودة آلية

الماء المستخدم قرب الحصاد أو في التصنيع يحتاج تقييماً صحياً قائماً على المخاطر. أعطال المضخات الكهربائية والمصادر الملوثة تحتاج مساعدة مؤهلة.

### Evidence and applicability limits

Add approved local weather data, water-source maps, laboratory routes, energy costs, pump constraints and crop profiles.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

يلزم إضافة طقس محلي معتمد وخرائط مصادر المياه ومسارات المختبر وكلفة الطاقة وقيود المضخات وملفات المحاصيل.

### Claim-level sources

- [ESDU-CLIMAT-AKKAR] ESDU/WFP climate-resilient livestock and rural livelihoods work in Akkar — https://www.aub.edu.lb/fafs/esdu/Documents/ToR_ESDU_Community%20mobilizer_WFP_Akkar%20.pdf
- [FAO-CROP-EVAPOTRANSPIRATION-56-2025] FAO. Crop evapotranspiration: Guidelines for computing crop water requirements, FAO Irrigation and Drainage Paper 56 Rev.1. 2025 revision. — https://openknowledge.fao.org/items/6c5c4d35-ba04-4cb5-8e78-95e9bb59922f
- [FAO-WATER-QUALITY-1985] FAO. Water quality for agriculture. 1985. — https://www.fao.org/4/t0234e/t0234e00.htm
- [UNDP-IRRIGATION-AKKAR] Support to host communities through irrigation and water-saving infrastructure — https://www.undp.org/lebanon/projects/support-host-communities-wash-sector
- [UNDP-LEBANON-NAP-2025] Lebanon National Adaptation Plan 2025–2035 — https://www.undp.org/lebanon/publications/lebanon-national-adaptation-plan-nap
- [WHO-GROWING-SAFER-PRODUCE-2012] World Health Organization. Five Keys to Growing Safer Fruits and Vegetables. 2012. — https://www.who.int/publications/i/item/9789241504003

## Integrated pest management and pesticide safety / الإدارة المتكاملة للآفات وسلامة المبيدات

```yaml
{
  "claim_ids": [
    "claim:kb-ipm-safety:guidance",
    "claim:kb-ipm-safety:decision",
    "claim:kb-ipm-safety:safety"
  ],
  "content_kind": "policy",
  "dynamicity": "live_only",
  "effective_from": null,
  "entities": [
    {
      "aliases": [],
      "id": "insect_pest",
      "label_ar": "آفة حشرية",
      "label_en": "insect pest",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "weed",
      "label_ar": "عشب ضار",
      "label_en": "weed",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "crop_rotation",
      "label_ar": "الدورة الزراعية",
      "label_en": "crop rotation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "scouting",
      "label_ar": "الكشف الحقلي",
      "label_en": "field scouting",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "IPM"
        },
        {
          "language": "arz",
          "script": "arabic",
          "text": "ادارة متكاملة"
        }
      ],
      "id": "ipm",
      "label_ar": "الإدارة المتكاملة للآفات",
      "label_en": "integrated pest management",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "sanitation",
      "label_ar": "النظافة الزراعية",
      "label_en": "farm sanitation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "nonchemical_control",
      "label_ar": "خفض الخطر من دون مواد كيميائية",
      "label_en": "non-chemical risk reduction",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "مبيد"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mabid"
        }
      ],
      "id": "pesticide",
      "label_ar": "مبيد زراعي",
      "label_en": "agricultural pesticide",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "glyphosate",
      "label_ar": "غليفوسات",
      "label_en": "glyphosate",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "moa_lebanon",
      "label_ar": "وزارة الزراعة اللبنانية",
      "label_en": "Lebanon Ministry of Agriculture",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "competent_authority",
      "label_ar": "السلطة المختصة",
      "label_en": "competent authority",
      "type": "organization"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مهندس زراعي"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mhandes zira3e"
        }
      ],
      "id": "agronomist",
      "label_ar": "مهندس زراعي مؤهل",
      "label_en": "qualified agronomist",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "pesticide_register",
      "label_ar": "سجل المبيدات الحالي",
      "label_en": "current pesticide register",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "product_label",
      "label_ar": "ملصق المنتج المسجل",
      "label_en": "registered product label",
      "type": "regulation"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "PHI"
        }
      ],
      "id": "preharvest_interval",
      "label_ar": "فترة ما قبل الحصاد",
      "label_en": "pre-harvest interval",
      "type": "regulation"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "REI"
        }
      ],
      "id": "reentry_interval",
      "label_ar": "فترة إعادة الدخول",
      "label_en": "re-entry interval",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "poisoning",
      "label_ar": "اشتباه تسمم",
      "label_en": "suspected poisoning",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "worker_exposure",
      "label_ar": "تعرض العامل لمادة كيميائية",
      "label_en": "worker chemical exposure",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "chemical_residue",
      "label_ar": "خطر المتبقيات الكيميائية",
      "label_en": "chemical residue risk",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "pesticide_use",
      "label_ar": "استخدام المبيدات",
      "label_en": "pesticide use",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "biodiversity",
      "label_ar": "التنوع الحيوي الزراعي",
      "label_en": "farm biodiversity",
      "type": "sustainability_impact"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-dynamic-information",
      "type": "requires_live_source"
    },
    {
      "target": "kb-referrals",
      "type": "escalates_to"
    }
  ],
  "id": "kb-ipm-safety",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [],
      "id": "insect_pest",
      "label_ar": "آفة حشرية",
      "label_en": "insect pest",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "weed",
      "label_ar": "عشب ضار",
      "label_en": "weed",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "crop_rotation",
      "label_ar": "الدورة الزراعية",
      "label_en": "crop rotation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "scouting",
      "label_ar": "الكشف الحقلي",
      "label_en": "field scouting",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "IPM"
        },
        {
          "language": "arz",
          "script": "arabic",
          "text": "ادارة متكاملة"
        }
      ],
      "id": "ipm",
      "label_ar": "الإدارة المتكاملة للآفات",
      "label_en": "integrated pest management",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "sanitation",
      "label_ar": "النظافة الزراعية",
      "label_en": "farm sanitation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "nonchemical_control",
      "label_ar": "خفض الخطر من دون مواد كيميائية",
      "label_en": "non-chemical risk reduction",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "مبيد"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mabid"
        }
      ],
      "id": "pesticide",
      "label_ar": "مبيد زراعي",
      "label_en": "agricultural pesticide",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "glyphosate",
      "label_ar": "غليفوسات",
      "label_en": "glyphosate",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "moa_lebanon",
      "label_ar": "وزارة الزراعة اللبنانية",
      "label_en": "Lebanon Ministry of Agriculture",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "competent_authority",
      "label_ar": "السلطة المختصة",
      "label_en": "competent authority",
      "type": "organization"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مهندس زراعي"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mhandes zira3e"
        }
      ],
      "id": "agronomist",
      "label_ar": "مهندس زراعي مؤهل",
      "label_en": "qualified agronomist",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "pesticide_register",
      "label_ar": "سجل المبيدات الحالي",
      "label_en": "current pesticide register",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "product_label",
      "label_ar": "ملصق المنتج المسجل",
      "label_en": "registered product label",
      "type": "regulation"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "PHI"
        }
      ],
      "id": "preharvest_interval",
      "label_ar": "فترة ما قبل الحصاد",
      "label_en": "pre-harvest interval",
      "type": "regulation"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "REI"
        }
      ],
      "id": "reentry_interval",
      "label_ar": "فترة إعادة الدخول",
      "label_en": "re-entry interval",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "poisoning",
      "label_ar": "اشتباه تسمم",
      "label_en": "suspected poisoning",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "worker_exposure",
      "label_ar": "تعرض العامل لمادة كيميائية",
      "label_en": "worker chemical exposure",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "chemical_residue",
      "label_ar": "خطر المتبقيات الكيميائية",
      "label_en": "chemical residue risk",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "pesticide_use",
      "label_ar": "استخدام المبيدات",
      "label_en": "pesticide use",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "biodiversity",
      "label_ar": "التنوع الحيوي الزراعي",
      "label_en": "farm biodiversity",
      "type": "sustainability_impact"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "scouting",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "ipm",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "sanitation",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "ipm",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "nonchemical_control",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "ipm",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "pesticide_register",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "pesticide",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "product_label",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "pesticide",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "preharvest_interval",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "product_label",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "reentry_interval",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "product_label",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "worker_exposure",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "pesticide",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "chemical_residue",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "pesticide",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "emergency_service",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "critical",
      "subject": "poisoning",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "emergency_service",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "critical",
      "subject": "worker_exposure",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "professional_referral",
      "polarity": "positive",
      "qualifiers": {
        "basis": "RAISE_product_policy"
      },
      "risk": "high",
      "subject": "glyphosate",
      "type": "prohibits"
    },
    {
      "evidence_section": "English guidance",
      "object": "pesticide_register",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "moa_lebanon",
      "type": "supported_by"
    },
    {
      "evidence_section": "English guidance",
      "object": "crop_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "insect_pest",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "pesticide_use",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "nonchemical_control",
      "type": "supports_action"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "high",
  "source_ids": [
    "FAO-LEBANON-PESTICIDE-CHILD-SAFETY",
    "FAO-WHO-PESTICIDE-CODE-2014",
    "MOA-BANNED-PESTICIDES-2026",
    "MOA-REGISTERED-PESTICIDES-2026"
  ],
  "supersedes_legacy_items": [
    "PESTICIDE-VERIFICATION-019",
    "SAFE-ADVICE-016",
    "WORKER-CHILD-SAFETY-020"
  ],
  "title_ar": "الإدارة المتكاملة للآفات وسلامة المبيدات",
  "title_en": "Integrated pest management and pesticide safety",
  "topics": [
    "pest",
    "IPM",
    "pesticide",
    "worker safety"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Lebanon's Ministry of Agriculture publishes current routes for registered and banned agricultural pesticides. A product must not be recommended merely because it was used previously or appears in an old guide. At the time of the decision, verify that the exact product and active ingredient are currently registered for the relevant crop and use, then follow the Arabic label, protective-equipment requirements, re-entry period, pre-harvest interval, storage, disposal, and resistance-management directions. The assistant should help a farmer assemble the crop, diagnosed problem, crop stage, product label, and timing information for a qualified adviser; it should not invent a spray program or interpret a missing or unreadable label as approval.

FAO and the Lebanese Ministry of Agriculture have specifically addressed child labour and occupational safety and health in agriculture and made pesticide-safety guidance available in Arabic. Keep children, pregnant people, untrained workers, animals, food, feed, and drinking-water containers away from mixing, spraying, treated areas during the restricted-entry period, and pesticide storage. Never transfer pesticides into beverage or food containers. Keep products locked in original labelled containers and wash work clothing separately. Suspected exposure, breathing difficulty, vomiting, confusion, burns, seizures, or collapse is an emergency: stop exposure, move to safety without exposing the rescuer, keep the label or product information, and contact emergency medical or poison-control support. Do not induce vomiting unless a qualified medical professional or the label explicitly instructs it.

The assistant supports decisions but does not replace an agronomist, veterinarian, laboratory, food-safety professional, engineer, or competent authority. It must avoid unsupported chemical or veterinary prescriptions, legal guarantees, and certain diagnoses from limited text or images. Escalate urgent animal illness, suspected poisoning, severe worker exposure, contaminated food or water, rapidly spreading crop loss, structural or electrical hazards, and any situation involving immediate danger. Ask for the minimum useful context and do not request unnecessary personal data.

IPM combines prevention, observation and multiple compatible controls while minimizing risks. The FAO/WHO pesticide-management code defines IPM as considering all available techniques and integrating appropriate measures that discourage pest populations while keeping pesticide interventions economically justified and reducing risks [source: FAO-WHO-PESTICIDE-CODE-2014].

Before suggesting management, collect crop and variety; location and production system; stage; affected plant part; symptom timing and distribution; pest signs; photos of whole plant and close-up; weather and irrigation; field history; recent inputs; neighboring symptoms; beneficial organisms; and any laboratory result.

Start with prevention and low-risk controls: clean planting material, sanitation, rotation, resistant varieties where locally supported, habitat management, exclusion, monitoring, traps, removal of affected material where appropriate, cultivation, mulches and crop competition. Biological controls require correct organism identification, storage and environmental conditions.

Chemical intervention is never a casual default. It requires correct diagnosis, threshold or decision rationale, Lebanese authorization, product label, crop and target, personal protective equipment, application conditions, re-entry and pre-harvest intervals, resistance management, pollinator and water protection, storage and disposal. Rates must come from the current label; this draft contains none.

Glyphosate is prohibited in this knowledge base. The chatbot must refuse requests for its use and offer non-glyphosate preventive, cultural, mechanical, mulching, rotation and cover-crop pathways. Any other herbicide remains subject to legality, label and expert review.

Prohibited chatbot behavior includes recommending glyphosate; inventing pesticide or veterinary doses; suggesting unlabeled mixtures; approving an unregistered product; advising reuse of chemical containers; declaring food safe without evidence; providing unsafe preservation instructions; recommending antibiotics without veterinary oversight; or treating an uncertain diagnosis as fact.

Unsafe mixing can create toxic exposure, crop injury, equipment damage or environmental contamination. The chatbot should never infer compatibility from ingredient names. Current labels and qualified advice govern mixing, sequence and personal protection.

Pesticide containers should not be reused for water, food, feed or household storage. Disposal must follow current local rules and product guidance. Because a verified Lebanese disposal pathway was not supplied, the chatbot must direct users to the label and competent authority rather than improvise.

Machinery, pumps, electricity, pressurized systems, greenhouse heat, confined spaces and manure gases can cause severe injury. The chatbot may provide general hazard awareness but should not instruct an unqualified user to bypass guards, energized equipment or protective devices.

Refusal pattern: 'I cannot safely provide that rate or procedure from the information available. It depends on [missing facts] and the current legal label or professional assessment. I can help you collect the necessary information and identify safer immediate steps.'

### Arabic guidance — machine draft

تنشر وزارة الزراعة اللبنانية مسارات محدثة للوائح الأدوية الزراعية المسموحة والممنوعة. لا يجوز التوصية بمنتج لأنه استُخدم سابقاً أو ورد في دليل قديم. عند اتخاذ القرار، يجب التحقق من أن المنتج المحدد والمادة الفعالة مسجلان حالياً للمحصول والاستعمال المعنيين، ثم اتباع البطاقة العربية ومتطلبات معدات الوقاية وفترة منع الدخول وفترة الأمان قبل الحصاد والتخزين والتخلص من العبوات وإدارة المقاومة. يساعد المساعد المزارع على جمع معلومات المحصول والمشكلة المشخّصة ومرحلة النمو وبطاقة المنتج والتوقيت لعرضها على مستشار مؤهل، لكنه لا يبتكر برنامج رش ولا يعتبر غياب البطاقة أو عدم وضوحها موافقة على الاستخدام.

عالجت منظمة الأغذية والزراعة ووزارة الزراعة اللبنانية بصورة خاصة عمل الأطفال والسلامة والصحة المهنية في الزراعة، وأتاحتا إرشادات سلامة المبيدات باللغة العربية. يجب إبعاد الأطفال والحوامل والعمال غير المدرّبين والحيوانات والغذاء والأعلاف وعبوات مياه الشرب عن الخلط والرش والمناطق المعالجة خلال فترة منع الدخول ومكان تخزين المبيدات. لا يُنقل المبيد أبداً إلى عبوة شراب أو غذاء، ويُحفظ مقفلاً في عبوته الأصلية التي تحمل البطاقة، وتُغسل ملابس العمل منفصلة. الاشتباه بالتعرض أو صعوبة التنفس أو القيء أو الارتباك أو الحروق أو الاختلاجات أو الانهيار حالة طارئة: يوقف التعرض ويُنقل المصاب إلى الأمان من دون تعريض المنقذ، وتُحفظ بطاقة المنتج أو معلوماته، ويُطلب فوراً دعم طبي طارئ أو مركز السموم. لا يُحفَّز القيء إلا إذا طلب مختص طبي مؤهل أو بطاقة المنتج ذلك صراحة.

يساعد المساعد في اتخاذ القرار لكنه لا يحل محل المهندس الزراعي أو الطبيب البيطري أو المختبر أو مختص سلامة الغذاء أو المهندس أو الجهة الرسمية المختصة. يجب أن يتجنب وصف مواد كيميائية أو أدوية بيطرية من دون سند، أو تقديم ضمانات قانونية، أو إعطاء تشخيص مؤكد انطلاقاً من نص أو صورة محدودة. تُحال الحالات العاجلة مثل مرض الحيوان الشديد أو الاشتباه بالتسمم أو تعرض العامل لمادة خطرة أو تلوث الغذاء أو المياه أو الخسارة السريعة الانتشار في المحصول أو الأخطار الإنشائية والكهربائية وأي خطر فوري. ويُطلب الحد الأدنى من المعلومات المفيدة من دون جمع بيانات شخصية غير ضرورية.

تجمع الإدارة المتكاملة للآفات بين الوقاية والرصد ووسائل متوافقة متعددة، مع تقليل مخاطر التدخل الكيميائي [source: FAO-WHO-PESTICIDE-CODE-2014]. قبل اقتراح المكافحة، اجمع المحصول والصنف والموقع والنظام والمرحلة والجزء المصاب وبداية العرض وتوزعه وعلامات الآفة وصور النبات كاملاً والتفاصيل والطقس والري وتاريخ الحقل والمدخلات الحديثة والأعراض المجاورة والكائنات النافعة وأي نتيجة مختبر.

ابدأ بمادة إكثار نظيفة والنظافة والدورة والمقاومة المعتمدة محلياً وإدارة الموئل والمنع والرصد والمصائد وإزالة الأجزاء عند ملاءمتها والعزيق والملش والتنافس. تتطلب المكافحة الحيوية تعريف الكائن الصحيح وشروط حفظه وبيئته.

لا يكون التدخل الكيميائي خياراً افتراضياً. يحتاج تشخيصاً صحيحاً وعتبة أو مبرراً، وترخيصاً لبنانياً حالياً، وملصق المنتج والمحصول والهدف، ومعدات الوقاية وظروف التطبيق وفترة إعادة الدخول وما قبل الحصاد وإدارة المقاومة وحماية الملقحات والمياه والتخزين والتخلص. تؤخذ الجرعة من الملصق الحالي فقط؛ لا تحتوي المسودة جرعات.

تنشر وزارة الزراعة مسارات القوائم الحالية للمبيدات المسجلة والممنوعة. لا يوصى بمنتج لأنه استُعمل سابقاً أو ورد في دليل قديم. يجب التحقق من المنتج والمادة الفعالة والاستعمال، ثم اتباع الملصق العربي والوقاية وفترات الدخول والحصاد والتخزين والتخلص. يساعد المساعد على جمع الملصق والمرحلة والتشخيص والتوقيت لخبير، ولا يخترع برنامج رش ولا يعتبر الملصق الغائب موافقة.

تمنع سياسة RAISE تقديم توصيات الغليفوسات، ويُعرض بدلاً منها المنع والعزيق والإزالة والملش والدورة ومحاصيل التغطية. ليست هذه دعوى عن الوضع القانوني. أي مبيد أعشاب آخر يخضع للقانون والملصق والخبير.

أبعد الأطفال والحوامل وغير المدرّبين والحيوانات والغذاء والعلف وعبوات ماء الشرب عن الخلط والرش والتخزين والمنطقة المعالجة خلال فترة المنع. لا تنقل المبيد إلى عبوة طعام أو شراب، واحفظه مقفلاً في عبوته الأصلية واغسل ملابس العمل منفصلة. لا تُعد استخدام العبوة ولا ترتجل مسار التخلص عند غياب مسار لبناني موثّق.

التعرض المشتبه به، أو صعوبة التنفس، أو القيء، أو الارتباك، أو الحروق، أو الاختلاجات، أو الانهيار طارئ: أوقف التعرض وانتقل إلى الأمان من دون تعريض المنقذ، واحفظ الملصق، واتصل بطوارئ طبية أو سموم مؤهلة. لا تُحدث القيء إلا إذا نص الملصق أو مختص طبي.

السلوك المحظور يشمل اختراع جرعات مبيد أو دواء بيطري، وخلطات غير مذكورة على الملصق، واعتماد منتج غير مسجل، وإعادة العبوات، واعتماد الغذاء آمناً بلا دليل، وإجراءات حفظ غير آمنة، ومضاد حيوي بلا طبيب، وتحويل الاحتمال إلى تشخيص. لا تُستنتج قابلية خلط المواد من أسمائها. كما لا تُعطَ تعليمات لتجاوز حواجز الآلات أو العمل على كهرباء أو ضغط أو مكان محصور بطريقة غير مؤهلة.

صيغة الرفض المفيدة: لا أستطيع إعطاء هذه الجرعة أو العملية بأمان من المعلومات المتاحة؛ فهي تعتمد على الحقائق الناقصة والملصق القانوني الحالي أو التقييم المهني. يمكنني مساعدتك في جمع المعلومات وتحديد خطوات فورية أقل خطراً.

### Decision logic

If identification or legal status is uncertain, provide no chemical selection or rate. Offer evidence collection, non-chemical risk reduction and specialist referral.

When the requested action could cause serious harm and required evidence is missing, refuse the action-level instruction and provide risk-reduction and escalation.

### منطق القرار — مسودة آلية

إذا كان التعريف أو الوضع القانوني غير مؤكّد فلا تختَر مادة ولا جرعة؛ قدّم جمع الأدلة وخفض الخطر بوسائل غير كيميائية وإحالة. وإذا كان الفعل قد يسبب ضرراً جسيماً والأدلة المطلوبة ناقصة، ارفض التعليمات التنفيذية واذكر الوقاية والتصعيد.

### Safe next action

Use a scouting record with date, location, crop stage, count or incidence method, photos, weather, action and result. Compare trends rather than reacting to one observation.

Attach safety categories to chunks and test that retrieval cannot bypass a refusal by paraphrasing an unsafe request.

### الخطوة التالية الآمنة — مسودة آلية

استخدم سجل كشف يذكر التاريخ والمكان ومرحلة المحصول وطريقة العد أو نسبة الإصابة والصور والطقس والفعل والنتيجة، وقارن الاتجاه لا ملاحظة واحدة. اربط فئات السلامة بالمقاطع واختبر أن إعادة صياغة الطلب غير الآمن لا تتجاوز الرفض.

### Avoid or escalate

Suspected human or animal poisoning is an emergency. Stop exposure where safe, preserve the label and seek qualified medical or toxicological help.

This chapter itself is mandatory retrieval context for chemical, veterinary, processing and machinery requests.

### ما يجب تجنبه أو تصعيده — مسودة آلية

الاشتباه بتسمم إنسان أو حيوان طارئ: أوقف التعرض حيث يكون ذلك آمناً، واحفظ الملصق، واطلب مساعدة طبية أو سمّية مؤهلة. هذا السجل سياق إلزامي لأي طلب كيميائي أو بيطري أو تصنيعي أو متعلق بالآلات.

### Evidence and applicability limits

Create expert-approved pest profiles for priority crops, including local names, look-alikes, seasonal occurrence, thresholds, legal products and non-chemical options.

Validate Lebanese chemical regulation, disposal pathways, poison support, occupational safety and emergency contacts before production.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

يلزم إعداد ملفات آفات معتمدة للمحاصيل ذات الأولوية، تشمل الأسماء المحلية والمتشابهات والموسم والعتبات والمنتجات القانونية والبدائل. يجب التحقق من القواعد اللبنانية والتخلص من العبوات ودعم السموم والسلامة المهنية وجهات الطوارئ قبل الإنتاج.

### Claim-level sources

- [FAO-LEBANON-PESTICIDE-CHILD-SAFETY] Protect Children from Pesticides guide released in Arabic — https://www.fao.org/lebanon/news/detail/FAO-releases-Protect-Children-from-Pesticides%21-Guide-in-Arabic/en
- [FAO-WHO-PESTICIDE-CODE-2014] FAO and WHO. International Code of Conduct on Pesticide Management. 2014, updated guidance available. — https://www.fao.org/pest-and-pesticide-management/pesticide-risk-reduction/code-conduct/en/
- [MOA-BANNED-PESTICIDES-2026] Current Ministry route for banned agricultural pesticides — https://www.agriculture.gov.lb/Subjects/Plant-Resources/Plant-Pharmacy/Banned-Pesticides
- [MOA-REGISTERED-PESTICIDES-2026] Current list of registered agricultural pesticides — https://www.agriculture.gov.lb/Subjects/Plant-Resources/Plant-Pharmacy/%D8%A7%D9%84%D8%A7%D8%AF%D9%88%D9%8A%D8%A9-%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D9%8A%D8%A9-%D8%A7%D9%84%D9%85%D8%B3%D9%85%D9%88%D8%AD%D8%A9

## Climate and seasonal decision support / دعم القرارات المناخية والموسمية

```yaml
{
  "claim_ids": [
    "claim:kb-climate-season:guidance",
    "claim:kb-climate-season:decision",
    "claim:kb-climate-season:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "live_only",
  "effective_from": null,
  "entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "3akkar"
        }
      ],
      "id": "akkar",
      "label_ar": "عكار",
      "label_en": "Akkar",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "planting",
      "label_ar": "مرحلة الزراعة",
      "label_en": "planting stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "flowering",
      "label_ar": "مرحلة الإزهار",
      "label_en": "flowering stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "crop_calendar",
      "label_ar": "تقويم زراعي تكيفي",
      "label_en": "adaptive crop calendar",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "rainwater_harvesting",
      "label_ar": "حصاد مياه الأمطار",
      "label_en": "rainwater harvesting",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "heat",
      "label_ar": "إجهاد حراري",
      "label_en": "heat stress",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "frost",
      "label_ar": "التعرض للصقيع",
      "label_en": "frost exposure",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "drought",
      "label_ar": "الجفاف",
      "label_en": "drought",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "extreme_weather",
      "label_ar": "طقس متطرف",
      "label_en": "extreme weather",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "precipitation_decline",
      "label_ar": "تراجع الهطول",
      "label_en": "declining precipitation",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "planting_window",
      "label_ar": "نافذة الزراعة",
      "label_en": "planting window",
      "type": "season"
    },
    {
      "aliases": [],
      "id": "harvest_window",
      "label_ar": "نافذة الحصاد",
      "label_en": "harvest window",
      "type": "season"
    },
    {
      "aliases": [],
      "id": "alert_window",
      "label_ar": "نافذة التنبيه الحالية",
      "label_en": "current alert window",
      "type": "season"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "LARI"
        },
        {
          "language": "arz",
          "script": "arabic",
          "text": "لاري"
        }
      ],
      "id": "lari",
      "label_ar": "مصلحة الأبحاث العلمية الزراعية",
      "label_en": "Lebanese Agricultural Research Institute",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "soil_conservation",
      "label_ar": "حفظ التربة",
      "label_en": "soil conservation",
      "type": "sustainability_impact"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-dynamic-information",
      "type": "requires_live_source"
    }
  ],
  "id": "kb-climate-season",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "3akkar"
        }
      ],
      "id": "akkar",
      "label_ar": "عكار",
      "label_en": "Akkar",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "planting",
      "label_ar": "مرحلة الزراعة",
      "label_en": "planting stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "flowering",
      "label_ar": "مرحلة الإزهار",
      "label_en": "flowering stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "crop_calendar",
      "label_ar": "تقويم زراعي تكيفي",
      "label_en": "adaptive crop calendar",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "rainwater_harvesting",
      "label_ar": "حصاد مياه الأمطار",
      "label_en": "rainwater harvesting",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "heat",
      "label_ar": "إجهاد حراري",
      "label_en": "heat stress",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "frost",
      "label_ar": "التعرض للصقيع",
      "label_en": "frost exposure",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "drought",
      "label_ar": "الجفاف",
      "label_en": "drought",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "extreme_weather",
      "label_ar": "طقس متطرف",
      "label_en": "extreme weather",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "precipitation_decline",
      "label_ar": "تراجع الهطول",
      "label_en": "declining precipitation",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "planting_window",
      "label_ar": "نافذة الزراعة",
      "label_en": "planting window",
      "type": "season"
    },
    {
      "aliases": [],
      "id": "harvest_window",
      "label_ar": "نافذة الحصاد",
      "label_en": "harvest window",
      "type": "season"
    },
    {
      "aliases": [],
      "id": "alert_window",
      "label_ar": "نافذة التنبيه الحالية",
      "label_en": "current alert window",
      "type": "season"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "LARI"
        },
        {
          "language": "arz",
          "script": "arabic",
          "text": "لاري"
        }
      ],
      "id": "lari",
      "label_ar": "مصلحة الأبحاث العلمية الزراعية",
      "label_en": "Lebanese Agricultural Research Institute",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "soil_conservation",
      "label_ar": "حفظ التربة",
      "label_en": "soil conservation",
      "type": "sustainability_impact"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "akkar",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "crop_calendar",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "planting_window",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "crop_calendar",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "harvest_window",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "crop_calendar",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "water_reliability",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "crop_calendar",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "alert_window",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "crop_calendar",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "wilting",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "heat",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "water_reliability",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "drought",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "drought",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "precipitation_decline",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "lari",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "extreme_weather",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "planting_window",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "frost",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "drought",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "soil_conservation",
      "type": "supports_action"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [
    "UNDP-LEBANON-NAP-2025"
  ],
  "supersedes_legacy_items": [
    "CLIMATE-RISK-014"
  ],
  "title_ar": "دعم القرارات المناخية والموسمية",
  "title_en": "Climate and seasonal decision support",
  "topics": [
    "climate",
    "season",
    "calendar",
    "adaptation"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Lebanon's National Adaptation Plan describes growing exposure to higher temperatures, declining precipitation, longer droughts, and extreme events. Seasonal calendars remain useful as a starting point, but should be adjusted using locality, altitude, observed crop stage, recent weather, water availability, and current extension alerts. A responsible answer identifies the decision window and what the farmer should observe rather than presenting one date as guaranteed. Long-term investment advice should consider water security, heat and frost exposure, soil protection, crop or livelihood diversification, and market risk.

Weather describes short-term atmospheric conditions; climate describes longer-term patterns and variability. A current forecast cannot be frozen into this document. The knowledge base should store interpretation rules, thresholds approved by experts and fallback behavior, while live observations and forecasts are retrieved from an approved service.

Seasonal decisions should combine crop or livestock sensitivity, growth stage, soil water, infrastructure, lead time, forecast uncertainty and consequence of error. A low-probability frost may justify action for a highly sensitive and valuable crop if the protective measure is feasible and low-risk.

General risk reduction includes maintaining drainage, securing greenhouse covers, checking pumps and backup power, planning water storage, protecting feed and inputs, providing shade and ventilation, avoiding unnecessary handling during heat and maintaining communication and referral plans.

Crop calendars must be local and versioned by elevation and production system. This draft does not provide planting dates. Climate variability and market timing mean a calendar should be a decision aid, not a guarantee.

Dynamic-source record: provider, geographic resolution, update interval, timestamp, forecast horizon, variables, known limits, outage behavior and citation. If the service fails, disclose failure and avoid claiming current conditions.

### Arabic guidance — machine draft

تشير الخطة الوطنية للتكيف في لبنان إلى ازدياد التعرض لارتفاع الحرارة وتراجع الهطول وطول فترات الجفاف والظواهر المتطرفة. تبقى الروزنامة الموسمية نقطة انطلاق مفيدة، لكن يجب تعديلها بحسب الموقع والارتفاع ومرحلة نمو المحصول المرصودة والطقس الحديث وتوفر المياه والتنبيهات الإرشادية الحالية. يحدد الجواب المسؤول نافذة القرار وما ينبغي للمزارع مراقبته بدلاً من تقديم تاريخ واحد على أنه مضمون. ويجب أن يراعي الاستثمار طويل الأجل أمن المياه والتعرض للحر والصقيع وحماية التربة وتنويع المحاصيل أو سبل العيش ومخاطر السوق.

تصف خطة التكيف الوطنية تعرض لبنان لحرارة أعلى وهطول أقل وفترات جفاف أطول وأحداث متطرفة. التقويم الموسمي نقطة بداية فقط، ويُعدّل حسب الموقع والارتفاع ومرحلة المحصول المرصودة والطقس الحديث والمياه والتنبيهات الحالية. يجب تحديد نافذة القرار وما يراقبه المزارع، لا ضمان تاريخ واحد. ويأخذ الاستثمار الطويل أمن المياه والحر والصقيع وحماية التربة والتنويع ومخاطر السوق.

الطقس حالة قصيرة المدى والمناخ نمط طويل المدى. لا تُخزن النشرة الحالية كحقيقة دائمة؛ تُخزن قواعد التفسير والعتبات التي يعتمدها الخبراء وسلوك التعطل، وتُجلب المشاهدات والتوقعات من خدمة معتمدة.

يجمع القرار حساسية المحصول أو الحيوان ومرحلته وماء التربة والبنية ومدة الاستعداد وعدم يقين التوقع وعاقبة الخطأ. قد يبرر احتمال صقيع منخفض حماية محصول حساس وعالي القيمة إذا كان الإجراء ممكناً وقليل الخطر.

تشمل الوقاية العامة صيانة الصرف وتثبيت أغطية البيوت وفحص المضخات والطاقة الاحتياطية وتخطيط تخزين الماء وحماية العلف والمدخلات وتوفير الظل والتهوية وتقليل المناولة وقت الحر والحفاظ على الاتصال والإحالة. يجب أن تكون تقاويم المحاصيل محلية ومؤرخة حسب الارتفاع والنظام؛ لا تقدم المسودة مواعيد زراعة.

يسجّل المصدر الحي المزوّد والدقة الجغرافية ودورة التحديث والطابع الزمني وأفق التوقع والمتغيرات والحدود وسلوك الانقطاع والاستشهاد. عند فشل الخدمة يُعلن الفشل ولا تُدّعى حالة حالية.

### Decision logic

For severe weather, prioritize official alerts. Do not advise travel or emergency action based solely on a model-generated interpretation.

### منطق القرار — مسودة آلية

في الطقس الشديد تُقدّم التنبيهات الرسمية. لا تنصح بالسفر أو بإجراء طارئ اعتماداً على تفسير مولّد وحده.

### Safe next action

Translate a forecast into decisions only after asking what is exposed, at what stage, what protection is available and what the consequences are.

### الخطوة التالية الآمنة — مسودة آلية

لا تحوّل التوقع إلى قرار قبل معرفة ما هو معرّض وفي أي مرحلة، وما الحماية المتاحة، وما عاقبة الفعل أو عدمه.

### Avoid or escalate

Forecasts are uncertain. The chatbot must show timestamps and must not guarantee frost, rainfall, yield or safety.

### ما يجب تجنبه أو تصعيده — مسودة آلية

التوقع غير يقيني؛ أظهر زمنه ولا تضمن الصقيع أو المطر أو المحصول أو السلامة.

### Evidence and applicability limits

Select and validate weather stations and forecast providers for Akkar; document elevation coverage and known gaps.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

يجب اختيار محطات وخدمات توقع معتمدة لعكار وتوثيق تغطية الارتفاعات والفجوات المعروفة.

### Claim-level sources

- [UNDP-LEBANON-NAP-2025] Lebanon National Adaptation Plan 2025–2035 — https://www.undp.org/lebanon/publications/lebanon-national-adaptation-plan-nap

## Greenhouse crop decisions / قرارات محاصيل البيوت المحمية

```yaml
{
  "claim_ids": [
    "claim:kb-greenhouse:guidance",
    "claim:kb-greenhouse:decision",
    "claim:kb-greenhouse:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "بندورة"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "banadoura"
        }
      ],
      "id": "tomato",
      "label_ar": "البندورة",
      "label_en": "tomato",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "cucumber",
      "label_ar": "الخيار",
      "label_en": "cucumber",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "leafy_herb",
      "label_ar": "عشبة ورقية",
      "label_en": "leafy herb",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "vegetative",
      "label_ar": "مرحلة النمو الخضري",
      "label_en": "vegetative stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "leaf_spot",
      "label_ar": "بقع الأوراق",
      "label_en": "leaf spot",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "insect_pest",
      "label_ar": "آفة حشرية",
      "label_en": "insect pest",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "crop_disease",
      "label_ar": "مرض نباتي",
      "label_en": "crop disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "scouting",
      "label_ar": "الكشف الحقلي",
      "label_en": "field scouting",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "sanitation",
      "label_ar": "النظافة الزراعية",
      "label_en": "farm sanitation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "drip_maintenance",
      "label_ar": "صيانة نظام التنقيط",
      "label_en": "drip-system maintenance",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "greenhouse_system",
      "label_ar": "نظام إنتاج في الدفيئة",
      "label_en": "greenhouse production system",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "ventilation",
      "label_ar": "تهوية الدفيئة",
      "label_en": "greenhouse ventilation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "shade_management",
      "label_ar": "إدارة التظليل",
      "label_en": "shade management",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "record_keeping",
      "label_ar": "حفظ سجلات المزرعة",
      "label_en": "farm record keeping",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مي الري"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mayy el ray"
        }
      ],
      "id": "irrigation_water",
      "label_ar": "مياه الري",
      "label_en": "irrigation water",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "energy_input",
      "label_ar": "مدخلات الطاقة",
      "label_en": "energy input",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "water_quality",
      "label_ar": "نوعية المياه",
      "label_en": "water quality",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "water_reliability",
      "label_ar": "موثوقية مصدر المياه",
      "label_en": "water-source reliability",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "heat",
      "label_ar": "إجهاد حراري",
      "label_en": "heat stress",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "humidity",
      "label_ar": "رطوبة مرتفعة",
      "label_en": "high humidity",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "energy_use",
      "label_ar": "استخدام الطاقة",
      "label_en": "energy use",
      "type": "sustainability_impact"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-water-irrigation",
      "type": "depends_on"
    },
    {
      "target": "kb-ipm-safety",
      "type": "depends_on"
    }
  ],
  "id": "kb-greenhouse",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "بندورة"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "banadoura"
        }
      ],
      "id": "tomato",
      "label_ar": "البندورة",
      "label_en": "tomato",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "cucumber",
      "label_ar": "الخيار",
      "label_en": "cucumber",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "leafy_herb",
      "label_ar": "عشبة ورقية",
      "label_en": "leafy herb",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "vegetative",
      "label_ar": "مرحلة النمو الخضري",
      "label_en": "vegetative stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "leaf_spot",
      "label_ar": "بقع الأوراق",
      "label_en": "leaf spot",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "insect_pest",
      "label_ar": "آفة حشرية",
      "label_en": "insect pest",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "crop_disease",
      "label_ar": "مرض نباتي",
      "label_en": "crop disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "scouting",
      "label_ar": "الكشف الحقلي",
      "label_en": "field scouting",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "sanitation",
      "label_ar": "النظافة الزراعية",
      "label_en": "farm sanitation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "drip_maintenance",
      "label_ar": "صيانة نظام التنقيط",
      "label_en": "drip-system maintenance",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "greenhouse_system",
      "label_ar": "نظام إنتاج في الدفيئة",
      "label_en": "greenhouse production system",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "ventilation",
      "label_ar": "تهوية الدفيئة",
      "label_en": "greenhouse ventilation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "shade_management",
      "label_ar": "إدارة التظليل",
      "label_en": "shade management",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "record_keeping",
      "label_ar": "حفظ سجلات المزرعة",
      "label_en": "farm record keeping",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مي الري"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mayy el ray"
        }
      ],
      "id": "irrigation_water",
      "label_ar": "مياه الري",
      "label_en": "irrigation water",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "energy_input",
      "label_ar": "مدخلات الطاقة",
      "label_en": "energy input",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "water_quality",
      "label_ar": "نوعية المياه",
      "label_en": "water quality",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "water_reliability",
      "label_ar": "موثوقية مصدر المياه",
      "label_en": "water-source reliability",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "heat",
      "label_ar": "إجهاد حراري",
      "label_en": "heat stress",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "humidity",
      "label_ar": "رطوبة مرتفعة",
      "label_en": "high humidity",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "energy_use",
      "label_ar": "استخدام الطاقة",
      "label_en": "energy use",
      "type": "sustainability_impact"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "ventilation",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "greenhouse_system",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "humidity",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "greenhouse_system",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "water_reliability",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "greenhouse_system",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "tomato",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "ventilation",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "cucumber",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "ventilation",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "crop_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "humidity",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "greenhouse_system",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "drip_maintenance",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "vegetative",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "irrigation_scheduling",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "heat",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "shade_management",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "water_reliability",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "energy_input",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "crop_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "scouting",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "diagnosis_workflow",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "record_keeping",
      "type": "supports_action"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [
    "ESDU-FARMING-FOR-ALL",
    "FAO-GREENHOUSE-GAP-2013",
    "MOA-AKKAR-GREENHOUSE-2026"
  ],
  "supersedes_legacy_items": [
    "GREENHOUSE-DECISIONS-004"
  ],
  "title_ar": "قرارات محاصيل البيوت المحمية",
  "title_en": "Greenhouse crop decisions",
  "topics": [
    "practice",
    "greenhouse",
    "tomato",
    "cucumber"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Useful greenhouse advice begins with the structure and season, ventilation and humidity pattern, water source, irrigation schedule, soil or substrate, crop stage, plant density, recent fertilizer applications, and a clear description or image of symptoms. Separate climate-management problems from nutrition, irrigation, and pest or disease causes. Encourage record keeping for irrigation, inputs, harvest, and rejected produce. A static assistant should not diagnose from one symptom or prescribe restricted inputs. Escalate rapidly when symptoms spread, plants wilt suddenly, roots or stems rot, or food-safety and worker-exposure risks are possible.

Protected structures modify temperature, humidity, radiation, wind and rainfall exposure; they do not remove climate or disease risk. Poor ventilation can increase heat and humidity, while damaged covers, blocked vents, inadequate water or power failure can rapidly harm crops.

Hydroponic and soilless systems require reliable water quality, nutrient management, monitoring, sanitation, pumps and maintenance. Automation can improve consistency but adds sensors, calibration, control logic, spare parts and failure modes. A sensor reading should be checked against plant condition and an independent measurement when consequences are high.

Ventilation, shading, evaporative cooling and heating must be designed for local conditions and system scale. This draft provides no engineering sizing or fertigation recipes. FAO greenhouse guidance supports integrated management but local design and expert review remain necessary [source: FAO-GREENHOUSE-GAP-2013].

Disease prevention depends on clean planting material, sanitation, water and substrate management, airflow, humidity control, monitoring and safe worker practices. Recirculating systems can distribute a problem quickly; corrective disinfection requires crop- and system-specific expertise.

Economic feasibility should include structure, water treatment, pumps, energy, consumables, nutrients, labor, maintenance, crop losses, financing, technical support, market quality and downtime. A higher theoretical yield does not guarantee profit.

### Arabic guidance — machine draft

يبدأ الإرشاد المفيد للبيوت البلاستيكية بمعرفة نوع المنشأة والموسم، والتهوية ونمط الرطوبة، ومصدر المياه، وبرنامج الري، والتربة أو الوسط الزراعي، ومرحلة نمو المحصول، وكثافة النباتات، وآخر إضافات التسميد، ووصف واضح أو صورة للأعراض. يجب فصل مشكلات المناخ داخل البيت عن أسباب التغذية والري والآفات والأمراض. ويُستحسن تسجيل الري والمدخلات والقطاف والثمار المرفوضة. لا ينبغي للمساعد الثابت تشخيص المشكلة من عرض واحد أو وصف مدخلات مقيّدة. يجب التصعيد سريعاً عند انتشار الأعراض أو الذبول المفاجئ أو تعفن الجذور والسيقان أو احتمال وجود مخاطر على سلامة الغذاء أو العمال.

تبدأ نصيحة البيت المحمي بنوع المنشأة والموسم والتهوية والرطوبة ومصدر المياه وبرنامج الري والتربة أو الوسط ومرحلة المحصول والكثافة وآخر تسميد ووصف واضح وصور. افصل مشكلات المناخ عن التغذية والري والآفات والأمراض، وسجّل الري والمدخلات والحصاد والرفض. لا يشخّص المساعد من عرض واحد ولا يصف مدخلاً مقيداً، ويُصعّد عند الانتشار السريع أو الذبول المفاجئ أو تعفن الجذور والساق أو مخاطر الغذاء والعمال.

تغير المنشأة الحرارة والرطوبة والإشعاع والرياح والمطر ولا تلغي الخطر. سوء التهوية يرفع الحر والرطوبة، وتلف الغطاء أو انسداد الفتحات أو نقص الماء أو انقطاع الكهرباء قد يضر سريعاً.

تحتاج الزراعة المائية ومن دون تربة ماءً مناسباً وإدارة عناصر ومراقبة ونظافة ومضخات وصيانة. تضيف الأتمتة حساسات ومعايرة وتحكماً وقطع غيار وأنماط فشل. تحقق من قراءة الحساس بحالة النبات وقياس مستقل عندما تكون العاقبة كبيرة.

تصميم التهوية والتظليل والتبريد التبخيري والتدفئة مرتبط بالموقع والحجم؛ لا توجد هنا أبعاد هندسية أو وصفات تسميد عبر الري. الوقاية من المرض تعتمد مادة نظيفة ونظافة وإدارة الماء والوسط وتدفق الهواء والرطوبة والرصد وسلامة العامل، وقد تنشر الدورة الراجعة المشكلة سريعاً، لذا يحتاج التطهير خبيراً خاصاً بالمحصول والنظام.

يدخل في الجدوى ثمن المنشأة ومعالجة الماء والمضخات والطاقة والمستهلكات والعناصر والعمل والصيانة والخسائر والتمويل والدعم الفني وجودة السوق والتوقف. المحصول النظري الأعلى لا يضمن الربح.

### Decision logic

If water or power reliability, technical support or market requirements are not known, present controlled-environment options as scenarios rather than a recommendation.

### منطق القرار — مسودة آلية

إذا لم تُعرف موثوقية الماء والطاقة والدعم الفني ومتطلبات السوق، اعرض خيارات البيئة المضبوطة كسيناريوهات لا كتوصية.

### Safe next action

Create an operations log for temperature, humidity, irrigation, pH/EC where relevant, alarms, calibration, maintenance, crop symptoms, interventions and downtime.

### الخطوة التالية الآمنة — مسودة آلية

أنشئ سجل تشغيل للحرارة والرطوبة والري والحموضة والموصلية عند الحاجة والإنذارات والمعايرة والصيانة والأعراض والتدخلات والتوقف.

### Avoid or escalate

Heat, electrical systems, pressure, chemicals and confined work require risk controls. No nutrient concentrate or disinfection rate is provided.

### ما يجب تجنبه أو تصعيده — مسودة آلية

الحرارة والكهرباء والضغط والمواد الكيميائية والعمل في مكان محصور تحتاج ضوابط خطر. لا تُعطى هنا كمية محلول مركز أو مطهر.

### Evidence and applicability limits

Validate greenhouse types, energy availability, summer heat, water quality, spare parts and technical service in Akkar.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

يجب التحقق من أنواع البيوت والطاقة وحر الصيف ونوعية الماء وقطع الغيار والخدمة الفنية في عكار.

### Claim-level sources

- [ESDU-FARMING-FOR-ALL] Farming For All: Introduction to Sustainable Agriculture — https://www.aub.edu.lb/cec/Pages/Farming-For-All.aspx
- [FAO-GREENHOUSE-GAP-2013] FAO. Good Agricultural Practices for greenhouse vegetable crops. 2013. — https://www.fao.org/3/i3284e/i3284e.pdf
- [MOA-AKKAR-GREENHOUSE-2026] Ministry monitoring of greenhouse and potato production in Akkar, March 2026 — https://www.agriculture.gov.lb/Media/News/2026/%D9%88%D8%B2%D8%A7%D8%B1%D8%A9-%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D8%A9-%D8%AA%D8%B1%D8%B5%D8%AF-%D8%AA%D8%B7%D9%88%D8%B1-%D8%A7%D9%84%D8%A7%D9%86%D8%AA%D8%A7%D8%AC-%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D9%8A-%D9%81%D9%8A-%D8%B9%D9%83%D8%A7%D8%B1-%D8%B2%D9%8A

## Harvest and post-harvest decisions / قرارات الحصاد وما بعد الحصاد

```yaml
{
  "claim_ids": [
    "claim:kb-postharvest:guidance",
    "claim:kb-postharvest:decision",
    "claim:kb-postharvest:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [],
      "id": "orchard_crop",
      "label_ar": "محصول بستاني",
      "label_en": "orchard crop",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "olive",
      "label_ar": "الزيتون",
      "label_en": "olive",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "apple",
      "label_ar": "التفاح",
      "label_en": "apple",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "citrus",
      "label_ar": "الحمضيات",
      "label_en": "citrus",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "avocado",
      "label_ar": "الأفوكادو",
      "label_en": "avocado",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "leafy_herb",
      "label_ar": "عشبة ورقية",
      "label_en": "leafy herb",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "harvest",
      "label_ar": "مرحلة الحصاد",
      "label_en": "harvest stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "postharvest",
      "label_ar": "مرحلة ما بعد الحصاد",
      "label_en": "post-harvest stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "storage",
      "label_ar": "مرحلة التخزين",
      "label_en": "storage stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "package_swelling",
      "label_ar": "انتفاخ العبوة",
      "label_en": "package swelling",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "off_odor",
      "label_ar": "رائحة غير طبيعية",
      "label_en": "unusual odor",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "rodent",
      "label_ar": "قارض",
      "label_en": "rodent",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "traceability",
      "label_ar": "التتبع",
      "label_en": "traceability",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "cold_chain",
      "label_ar": "إدارة سلسلة التبريد",
      "label_en": "cold-chain management",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "sorting",
      "label_ar": "فرز المنتج",
      "label_en": "produce sorting",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "waste_reduction",
      "label_ar": "خفض الهدر",
      "label_en": "waste reduction",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "harvest_window",
      "label_ar": "نافذة الحصاد",
      "label_en": "harvest window",
      "type": "season"
    },
    {
      "aliases": [],
      "id": "food_safety_specialist",
      "label_ar": "اختصاصي سلامة غذاء",
      "label_en": "food-safety specialist",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "buyer",
      "label_ar": "المشتري",
      "label_en": "buyer",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "fresh_market",
      "label_ar": "سوق المنتجات الطازجة",
      "label_en": "fresh produce market",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "processing_market",
      "label_ar": "سوق التصنيع",
      "label_en": "processing market",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "buyer_specification",
      "label_ar": "مواصفة المشتري",
      "label_en": "buyer specification",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "food_contamination",
      "label_ar": "تلوث الغذاء",
      "label_en": "food contamination",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "chemical_residue",
      "label_ar": "خطر المتبقيات الكيميائية",
      "label_en": "chemical residue risk",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "food_loss",
      "label_ar": "فقد الغذاء",
      "label_en": "food loss",
      "type": "sustainability_impact"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-business-markets",
      "type": "supports_action"
    }
  ],
  "id": "kb-postharvest",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [],
      "id": "orchard_crop",
      "label_ar": "محصول بستاني",
      "label_en": "orchard crop",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "olive",
      "label_ar": "الزيتون",
      "label_en": "olive",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "apple",
      "label_ar": "التفاح",
      "label_en": "apple",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "citrus",
      "label_ar": "الحمضيات",
      "label_en": "citrus",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "avocado",
      "label_ar": "الأفوكادو",
      "label_en": "avocado",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "leafy_herb",
      "label_ar": "عشبة ورقية",
      "label_en": "leafy herb",
      "type": "crop"
    },
    {
      "aliases": [],
      "id": "harvest",
      "label_ar": "مرحلة الحصاد",
      "label_en": "harvest stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "postharvest",
      "label_ar": "مرحلة ما بعد الحصاد",
      "label_en": "post-harvest stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "storage",
      "label_ar": "مرحلة التخزين",
      "label_en": "storage stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "package_swelling",
      "label_ar": "انتفاخ العبوة",
      "label_en": "package swelling",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "off_odor",
      "label_ar": "رائحة غير طبيعية",
      "label_en": "unusual odor",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "rodent",
      "label_ar": "قارض",
      "label_en": "rodent",
      "type": "pest"
    },
    {
      "aliases": [],
      "id": "traceability",
      "label_ar": "التتبع",
      "label_en": "traceability",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "cold_chain",
      "label_ar": "إدارة سلسلة التبريد",
      "label_en": "cold-chain management",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "sorting",
      "label_ar": "فرز المنتج",
      "label_en": "produce sorting",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "waste_reduction",
      "label_ar": "خفض الهدر",
      "label_en": "waste reduction",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "harvest_window",
      "label_ar": "نافذة الحصاد",
      "label_en": "harvest window",
      "type": "season"
    },
    {
      "aliases": [],
      "id": "food_safety_specialist",
      "label_ar": "اختصاصي سلامة غذاء",
      "label_en": "food-safety specialist",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "buyer",
      "label_ar": "المشتري",
      "label_en": "buyer",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "fresh_market",
      "label_ar": "سوق المنتجات الطازجة",
      "label_en": "fresh produce market",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "processing_market",
      "label_ar": "سوق التصنيع",
      "label_en": "processing market",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "buyer_specification",
      "label_ar": "مواصفة المشتري",
      "label_en": "buyer specification",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "food_contamination",
      "label_ar": "تلوث الغذاء",
      "label_en": "food contamination",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "chemical_residue",
      "label_ar": "خطر المتبقيات الكيميائية",
      "label_en": "chemical residue risk",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "food_loss",
      "label_ar": "فقد الغذاء",
      "label_en": "food loss",
      "type": "sustainability_impact"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "buyer_specification",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "harvest",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "postharvest",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "sorting",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "storage",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "cold_chain",
      "type": "applies_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "food_contamination",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "traceability",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "food_safety_specialist",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "package_swelling",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "food_safety_specialist",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "off_odor",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "buyer",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "food_contamination",
      "type": "prohibits"
    },
    {
      "evidence_section": "English guidance",
      "object": "food_loss",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "waste_reduction",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "buyer_specification",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "fresh_market",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "buyer_specification",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "processing_market",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "cold_chain",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "orchard_crop",
      "type": "requires_context"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [
    "CODEX-FOOD-HYGIENE-CXC1-2022",
    "ESDU-AKKAR-VALUECHAINS",
    "ESDU-ARDI-ARDAK",
    "ESDU-FARMING-FOR-ALL",
    "WHO-FIVE-KEYS-SAFER-FOOD-2006",
    "WHO-GROWING-SAFER-PRODUCE-2012"
  ],
  "supersedes_legacy_items": [
    "POSTHARVEST-MARKET-015"
  ],
  "title_ar": "قرارات الحصاد وما بعد الحصاد",
  "title_en": "Harvest and post-harvest decisions",
  "topics": [
    "production_stage",
    "harvest",
    "storage",
    "quality"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

A farmer's best decision may depend on the buyer and post-harvest chain before planting. Ask about intended market, buyer specifications, harvest maturity, sorting and rejected product, packaging, cooling or storage, transport time, processing options, payment terms, and records. Separate agronomic yield from saleable yield and net return. Do not present a dated market opportunity or grant as current without a live source and timestamp. Food-safety, licensing, and certification claims require current competent-authority information.

Harvest maturity depends on product, intended market, transport time and quality standard. Color alone may be inadequate. Product profiles should define approved maturity indicators and sampling methods.

Minimize injury, contamination and heat exposure during harvest. Use clean tools and containers, separate damaged or contaminated product, keep produce out of direct sun where feasible and move it through the required cooling or handling sequence promptly.

Water used for washing or cooling must be fit for its intended purpose and managed so it does not spread contamination. Clean-looking water is not proof of microbiological safety. Codex and WHO hygiene principles require control from primary production through handling [sources: CODEX-FOOD-HYGIENE-CXC1-2022, WHO-FIVE-KEYS-SAFER-FOOD-2006, WHO-GROWING-SAFER-PRODUCE-2012].

Storage conditions are commodity-specific. Temperature, relative humidity, ventilation, packaging, ethylene sensitivity, pest control and product compatibility matter. This draft intentionally provides no universal storage temperature or shelf life.

Traceability should connect lot, producer or field, harvest date, inputs where relevant, handlers, processing or storage steps, buyer and complaints. The level of detail should be proportionate and protect personal data.

### Arabic guidance — machine draft

قد يعتمد أفضل قرار للمزارع على المشتري وسلسلة ما بعد الحصاد قبل بدء الزراعة. يجب السؤال عن السوق المستهدف ومواصفات المشتري ومرحلة النضج عند القطاف والفرز والمنتج المرفوض والتوضيب والتبريد أو التخزين ومدة النقل وخيارات التصنيع وشروط الدفع والسجلات. ينبغي التمييز بين الإنتاج الزراعي والإنتاج القابل للبيع والعائد الصافي. لا يجوز عرض فرصة سوق أو منحة مؤرخة على أنها حالية من دون مصدر مباشر وتاريخ واضح. كما تتطلب ادعاءات سلامة الغذاء والترخيص والشهادات معلومات حديثة من الجهة المختصة.

قد يتحدد أفضل قرار قبل الزراعة بحسب المشتري وسلسلة ما بعد الحصاد. اسأل عن السوق ومواصفات المشتري ودرجة النضج والفرز والمنتج المرفوض والتعبئة والتبريد أو التخزين ومدة النقل والتصنيع وشروط الدفع والسجلات. افصل المحصول الزراعي عن القابل للبيع وصافي العائد، ولا تعرض فرصة أو منحة قديمة كحالية بلا مصدر حي وتاريخ.

يعتمد نضج الحصاد على المنتج والسوق ومدة النقل ومعيار الجودة؛ اللون وحده قد لا يكفي. يجب أن يحدد ملف المنتج مؤشرات نضج وطريقة عينة معتمدة.

قلل الجروح والتلوث والحر وقت الحصاد، واستعمل أدوات وعبوات نظيفة، وافصل التالف أو الملوث، وأبعد المنتج عن الشمس حيث أمكن، وانقله سريعاً ضمن مسار التبريد أو المعاملة المطلوب.

يجب أن تكون مياه الغسل أو التبريد ملائمة لغرضها وألا تنشر التلوث؛ صفاء الماء لا يثبت سلامته الميكروبية [sources: CODEX-FOOD-HYGIENE-CXC1-2022, WHO-FIVE-KEYS-SAFER-FOOD-2006, WHO-GROWING-SAFER-PRODUCE-2012]. تختلف ظروف التخزين حسب السلعة من حيث الحرارة والرطوبة والتهوية والتعبئة والحساسية للإيثيلين والآفات والتوافق؛ لا توجد درجة أو مدة موحدة في المسودة.

يربط التتبع الدفعة والمنتج أو الحقل وتاريخ الحصاد والمدخلات عند الحاجة والمناولين والتصنيع أو التخزين والمشتري والشكاوى، بقدر متناسب مع حماية البيانات.

### Decision logic

If a product has visible spoilage, unusual odor, package swelling, contamination exposure or temperature abuse, do not advise tasting it to decide safety; isolate and seek food-safety assessment.

### منطق القرار — مسودة آلية

إذا وُجد فساد ظاهر أو رائحة غير معتادة أو انتفاخ عبوة أو تعرض للتلوث أو إساءة حرارة، لا تنصح بالتذوق لاختبار السلامة؛ اعزل المنتج واطلب تقييماً مختصاً.

### Safe next action

Use a product profile and lot record rather than a generic storage answer. Monitor quality and temperature where relevant and document deviations.

### الخطوة التالية الآمنة — مسودة آلية

استخدم ملف منتج وسجل دفعة بدلاً من جواب تخزين عام، وراقب الجودة والحرارة حيث تلزم وسجّل أي انحراف.

### Avoid or escalate

The absence of visible spoilage does not prove safety. Product-specific food-safety review is required.

### ما يجب تجنبه أو تصعيده — مسودة آلية

غياب علامة الفساد لا يثبت السلامة. يلزم تقييم خاص بالمنتج لسلامة الغذاء.

### Evidence and applicability limits

Map cold-chain capacity, transport times, packaging availability and buyer specifications for priority value chains.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

يجب رسم قدرات سلسلة التبريد ومدة النقل وتوافر العبوات ومواصفات المشترين لسلاسل القيمة ذات الأولوية.

### Claim-level sources

- [CODEX-FOOD-HYGIENE-CXC1-2022] Codex Alimentarius Commission (FAO/WHO). General Principles of Food Hygiene (CXC 1-1969). 2022 edition. — https://openknowledge.fao.org/handle/20.500.14283/cc6125en
- [ESDU-AKKAR-VALUECHAINS] Value Chains for Improved Socioeconomic Well-being of Syrian Refugees and Lebanese Host Communities — https://www.aub.edu.lb/fafs/esdu/Pages/vcproject.aspx
- [ESDU-ARDI-ARDAK] Ardi Ardak National Food Security Initiative — https://www.aub.edu.lb/fafs/esdu/Pages/ardiardakinitiative.aspx
- [ESDU-FARMING-FOR-ALL] Farming For All: Introduction to Sustainable Agriculture — https://www.aub.edu.lb/cec/Pages/Farming-For-All.aspx
- [WHO-FIVE-KEYS-SAFER-FOOD-2006] World Health Organization. Five Keys to Safer Food Manual. 2006. — https://www.who.int/publications/i/item/9789241594639
- [WHO-GROWING-SAFER-PRODUCE-2012] World Health Organization. Five Keys to Growing Safer Fruits and Vegetables. 2012. — https://www.who.int/publications/i/item/9789241504003

## Food processing and food-safety boundaries / حدود تصنيع الغذاء وسلامته

```yaml
{
  "claim_ids": [
    "claim:kb-food-processing-safety:guidance",
    "claim:kb-food-processing-safety:decision",
    "claim:kb-food-processing-safety:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [],
      "id": "postharvest",
      "label_ar": "مرحلة ما بعد الحصاد",
      "label_en": "post-harvest stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "storage",
      "label_ar": "مرحلة التخزين",
      "label_en": "storage stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "package_swelling",
      "label_ar": "انتفاخ العبوة",
      "label_en": "package swelling",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "off_odor",
      "label_ar": "رائحة غير طبيعية",
      "label_en": "unusual odor",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "foodborne_disease",
      "label_ar": "مرض منقول بالغذاء",
      "label_en": "foodborne disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "traceability",
      "label_ar": "التتبع",
      "label_en": "traceability",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "cold_chain",
      "label_ar": "إدارة سلسلة التبريد",
      "label_en": "cold-chain management",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "HACCP"
        },
        {
          "language": "ar",
          "script": "arabic",
          "text": "هاسب"
        }
      ],
      "id": "haccp",
      "label_ar": "نظام تحليل المخاطر ونقاط التحكم الحرجة",
      "label_en": "HACCP system",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "hygiene",
      "label_ar": "ممارسات النظافة الجيدة",
      "label_en": "good hygiene practice",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "manure",
      "label_ar": "روث حيواني",
      "label_en": "manure",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "codex",
      "label_ar": "الدستور الغذائي",
      "label_en": "Codex Alimentarius",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "who",
      "label_ar": "منظمة الصحة العالمية",
      "label_en": "World Health Organization",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "competent_authority",
      "label_ar": "السلطة المختصة",
      "label_en": "competent authority",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "food_safety_specialist",
      "label_ar": "اختصاصي سلامة غذاء",
      "label_en": "food-safety specialist",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "food_licensing",
      "label_ar": "ترخيص المنشأة الغذائية",
      "label_en": "food-business licensing",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "food_contamination",
      "label_ar": "تلوث الغذاء",
      "label_en": "food contamination",
      "type": "risk"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-referrals",
      "type": "escalates_to"
    }
  ],
  "id": "kb-food-processing-safety",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [],
      "id": "postharvest",
      "label_ar": "مرحلة ما بعد الحصاد",
      "label_en": "post-harvest stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "storage",
      "label_ar": "مرحلة التخزين",
      "label_en": "storage stage",
      "type": "production_stage"
    },
    {
      "aliases": [],
      "id": "package_swelling",
      "label_ar": "انتفاخ العبوة",
      "label_en": "package swelling",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "off_odor",
      "label_ar": "رائحة غير طبيعية",
      "label_en": "unusual odor",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "foodborne_disease",
      "label_ar": "مرض منقول بالغذاء",
      "label_en": "foodborne disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "traceability",
      "label_ar": "التتبع",
      "label_en": "traceability",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "cold_chain",
      "label_ar": "إدارة سلسلة التبريد",
      "label_en": "cold-chain management",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "HACCP"
        },
        {
          "language": "ar",
          "script": "arabic",
          "text": "هاسب"
        }
      ],
      "id": "haccp",
      "label_ar": "نظام تحليل المخاطر ونقاط التحكم الحرجة",
      "label_en": "HACCP system",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "hygiene",
      "label_ar": "ممارسات النظافة الجيدة",
      "label_en": "good hygiene practice",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "manure",
      "label_ar": "روث حيواني",
      "label_en": "manure",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "codex",
      "label_ar": "الدستور الغذائي",
      "label_en": "Codex Alimentarius",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "who",
      "label_ar": "منظمة الصحة العالمية",
      "label_en": "World Health Organization",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "competent_authority",
      "label_ar": "السلطة المختصة",
      "label_en": "competent authority",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "food_safety_specialist",
      "label_ar": "اختصاصي سلامة غذاء",
      "label_en": "food-safety specialist",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "food_licensing",
      "label_ar": "ترخيص المنشأة الغذائية",
      "label_en": "food-business licensing",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "food_contamination",
      "label_ar": "تلوث الغذاء",
      "label_en": "food contamination",
      "type": "risk"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "food_contamination",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "hygiene",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "hygiene",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "haccp",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "codex",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "haccp",
      "type": "supported_by"
    },
    {
      "evidence_section": "English guidance",
      "object": "who",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "hygiene",
      "type": "supported_by"
    },
    {
      "evidence_section": "English guidance",
      "object": "food_licensing",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "postharvest",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "emergency_service",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "critical",
      "subject": "foodborne_disease",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "foodborne_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "package_swelling",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "competent_authority",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "food_contamination",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "haccp",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "traceability",
      "type": "supports_action"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "high",
  "source_ids": [
    "CODEX-FOOD-HYGIENE-CXC1-2022",
    "WHO-FIVE-KEYS-SAFER-FOOD-2006"
  ],
  "supersedes_legacy_items": [],
  "title_ar": "حدود تصنيع الغذاء وسلامته",
  "title_en": "Food processing and food-safety boundaries",
  "topics": [
    "risk",
    "processing",
    "food safety"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

A processing idea begins with the intended product and consumer, raw-material hazards, process flow, equipment, packaging, distribution and legal requirements. A traditional recipe is not automatically a validated commercial process.

Good hygiene practices are the foundation. Codex identifies food-business responsibilities across the chain and integrates HACCP-system principles [source: CODEX-FOOD-HYGIENE-CXC1-2022]. The WHO Five Keys—cleanliness, separation, thorough cooking, safe temperatures and safe water/raw materials—are useful communication principles but do not replace a product-specific hazard plan [source: WHO-FIVE-KEYS-SAFER-FOOD-2006].

Shelf life must be supported by product formulation, process control, packaging, storage conditions, microbiological or chemical evidence where appropriate and a defined acceptance criterion. The chatbot must not assign a shelf life from appearance or a generic recipe.

Labeling, allergen statements, claims, weights, dates and licensing are jurisdiction-specific and date-sensitive. This draft contains no confirmation of current Lebanese requirements.

Value addition should be evaluated through demand, quality specification, batch consistency, yield, equipment, labor, energy, packaging, compliance, waste, recalls and market testing. A higher selling price may not produce a higher margin.

### Arabic guidance — machine draft

تبدأ فكرة التصنيع بالمنتج والمستهلك المقصودين، ومخاطر المادة الخام، ومسار العملية، والمعدات والتعبئة والتوزيع والمتطلبات القانونية. الوصفة التقليدية ليست تلقائياً عملية تجارية موثقة.

الممارسات الصحية الجيدة هي الأساس. يحدد الدستور الغذائي مسؤوليات منشآت الغذاء عبر السلسلة ويدمج مبادئ الهاسب [source: CODEX-FOOD-HYGIENE-CXC1-2022]. مفاتيح منظمة الصحة العالمية الخمسة—النظافة، والفصل، والطهي الكافي، ودرجات الحرارة الآمنة، والمياه والمواد الخام الآمنة—مفيدة للتواصل لكنها لا تستبدل خطة مخاطر خاصة بالمنتج [source: WHO-FIVE-KEYS-SAFER-FOOD-2006].

تحتاج مدة الصلاحية إلى تركيبة المنتج وضبط العملية والتعبئة وظروف التخزين وأدلة ميكروبية أو كيميائية عند الحاجة ومعيار قبول محدد. لا يحدد المساعد الصلاحية من الشكل أو وصفة عامة.

الملصق والمحسسات والادعاءات والوزن والتواريخ والترخيص مرتبطة بالقانون والزمن؛ لا تؤكد المسودة المتطلبات اللبنانية الحالية. وتُقيّم القيمة المضافة بالطلب والمواصفة وثبات الدفعات والمردود والمعدات والعمل والطاقة والتعبئة والامتثال والنفايات والاستدعاء واختبار السوق، فالسعر الأعلى لا يعني هامشاً أعلى.

### Decision logic

Refuse preservation, canning, fermentation or shelf-life instructions when critical process controls are missing. Refer to a food scientist or competent authority.

### منطق القرار — مسودة آلية

ارفض تعليمات الحفظ أو التعليب أو التخمير أو تحديد الصلاحية عند غياب نقاط الضبط الحرجة، وأحل إلى اختصاصي غذاء أو سلطة مختصة.

### Safe next action

Develop a process-flow diagram, hazard analysis, batch record, cleaning plan, supplier specification, lot code and complaint/recall procedure with a food-safety professional.

### الخطوة التالية الآمنة — مسودة آلية

طوّر مع مختص مخطط تدفق للعملية وتحليل مخاطر وسجل دفعة وخطة تنظيف ومواصفات مورّد ورمز دفعة وإجراء شكاوى واستدعاء.

### Avoid or escalate

Do not tell a user that a product is safe because it smells or looks normal. High-risk foods and preservation processes require expert validation.

### ما يجب تجنبه أو تصعيده — مسودة آلية

لا تقل إن المنتج آمن لأن رائحته أو شكله طبيعي. الأغذية عالية الخطر وعمليات الحفظ تحتاج تحققاً خبيراً.

### Evidence and applicability limits

Validate applicable Lebanese food laws, licensing bodies, laboratories, labeling, cold chain and cooperative processing capacity.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

يجب التحقق من قوانين الغذاء اللبنانية والجهات المرخصة والمختبرات والملصقات وسلسلة التبريد وقدرة التصنيع التعاوني.

### Claim-level sources

- [CODEX-FOOD-HYGIENE-CXC1-2022] Codex Alimentarius Commission (FAO/WHO). General Principles of Food Hygiene (CXC 1-1969). 2022 edition. — https://openknowledge.fao.org/handle/20.500.14283/cc6125en
- [WHO-FIVE-KEYS-SAFER-FOOD-2006] World Health Organization. Five Keys to Safer Food Manual. 2006. — https://www.who.int/publications/i/item/9789241594639

## Farm business, value-chain, and market decisions / قرارات الأعمال الزراعية وسلاسل القيمة والأسواق

```yaml
{
  "claim_ids": [
    "claim:kb-business-markets:guidance",
    "claim:kb-business-markets:decision",
    "claim:kb-business-markets:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "live_only",
  "effective_from": null,
  "entities": [
    {
      "aliases": [],
      "id": "market_suited_variety",
      "label_ar": "صنف ملائم للسوق",
      "label_en": "market-suited variety",
      "type": "variety"
    },
    {
      "aliases": [],
      "id": "record_keeping",
      "label_ar": "حفظ سجلات المزرعة",
      "label_en": "farm record keeping",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "enterprise_budget",
      "label_ar": "موازنة المشروع الزراعي",
      "label_en": "enterprise budgeting",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "break_even_analysis",
      "label_ar": "تحليل نقطة التعادل",
      "label_en": "break-even analysis",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "sensitivity_analysis",
      "label_ar": "تحليل الحساسية",
      "label_en": "sensitivity analysis",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "waste_reduction",
      "label_ar": "خفض الهدر",
      "label_en": "waste reduction",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "energy_input",
      "label_ar": "مدخلات الطاقة",
      "label_en": "energy input",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "labor_input",
      "label_ar": "مدخلات العمل",
      "label_en": "labor input",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "cooperative",
      "label_ar": "تعاونية زراعية",
      "label_en": "farmer cooperative",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "market_information_service",
      "label_ar": "خدمة معلومات سوق مؤرخة",
      "label_en": "dated market-information service",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "buyer",
      "label_ar": "المشتري",
      "label_en": "buyer",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "fresh_market",
      "label_ar": "سوق المنتجات الطازجة",
      "label_en": "fresh produce market",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "processing_market",
      "label_ar": "سوق التصنيع",
      "label_en": "processing market",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "buyer_specification",
      "label_ar": "مواصفة المشتري",
      "label_en": "buyer specification",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "grant_opportunity",
      "label_ar": "إعلان منحة أو فرصة",
      "label_en": "grant or opportunity call",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "export_condition",
      "label_ar": "شرط تصدير",
      "label_en": "export condition",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "stale_information",
      "label_ar": "معلومات قديمة",
      "label_en": "stale information",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "fixed_cost",
      "label_ar": "تكلفة ثابتة",
      "label_en": "fixed cost",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "variable_cost",
      "label_ar": "تكلفة متغيرة",
      "label_en": "variable cost",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "working_capital",
      "label_ar": "رأس المال العامل",
      "label_en": "working capital",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "owner_labor",
      "label_ar": "عمل المالك",
      "label_en": "owner labor",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "financing_cost",
      "label_ar": "تكلفة التمويل",
      "label_en": "financing cost",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "depreciation",
      "label_ar": "الاستهلاك المحاسبي",
      "label_en": "depreciation",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "contribution_margin",
      "label_ar": "هامش المساهمة",
      "label_en": "contribution margin",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "break_even_price",
      "label_ar": "سعر التعادل",
      "label_en": "break-even price",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "break_even_yield",
      "label_ar": "إنتاج التعادل",
      "label_en": "break-even yield",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "water_use",
      "label_ar": "استخدام المياه",
      "label_en": "water use",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "fertilizer_loss",
      "label_ar": "فقد الأسمدة",
      "label_en": "fertilizer loss",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "pesticide_use",
      "label_ar": "استخدام المبيدات",
      "label_en": "pesticide use",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "energy_use",
      "label_ar": "استخدام الطاقة",
      "label_en": "energy use",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "labor_impact",
      "label_ar": "أثر العمل",
      "label_en": "labor impact",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "food_loss",
      "label_ar": "فقد الغذاء",
      "label_en": "food loss",
      "type": "sustainability_impact"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-dynamic-information",
      "type": "requires_live_source"
    }
  ],
  "id": "kb-business-markets",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [],
      "id": "market_suited_variety",
      "label_ar": "صنف ملائم للسوق",
      "label_en": "market-suited variety",
      "type": "variety"
    },
    {
      "aliases": [],
      "id": "record_keeping",
      "label_ar": "حفظ سجلات المزرعة",
      "label_en": "farm record keeping",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "enterprise_budget",
      "label_ar": "موازنة المشروع الزراعي",
      "label_en": "enterprise budgeting",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "break_even_analysis",
      "label_ar": "تحليل نقطة التعادل",
      "label_en": "break-even analysis",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "sensitivity_analysis",
      "label_ar": "تحليل الحساسية",
      "label_en": "sensitivity analysis",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "waste_reduction",
      "label_ar": "خفض الهدر",
      "label_en": "waste reduction",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "energy_input",
      "label_ar": "مدخلات الطاقة",
      "label_en": "energy input",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "labor_input",
      "label_ar": "مدخلات العمل",
      "label_en": "labor input",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "cooperative",
      "label_ar": "تعاونية زراعية",
      "label_en": "farmer cooperative",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "market_information_service",
      "label_ar": "خدمة معلومات سوق مؤرخة",
      "label_en": "dated market-information service",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "buyer",
      "label_ar": "المشتري",
      "label_en": "buyer",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "fresh_market",
      "label_ar": "سوق المنتجات الطازجة",
      "label_en": "fresh produce market",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "processing_market",
      "label_ar": "سوق التصنيع",
      "label_en": "processing market",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "buyer_specification",
      "label_ar": "مواصفة المشتري",
      "label_en": "buyer specification",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "grant_opportunity",
      "label_ar": "إعلان منحة أو فرصة",
      "label_en": "grant or opportunity call",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "export_condition",
      "label_ar": "شرط تصدير",
      "label_en": "export condition",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "stale_information",
      "label_ar": "معلومات قديمة",
      "label_en": "stale information",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "fixed_cost",
      "label_ar": "تكلفة ثابتة",
      "label_en": "fixed cost",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "variable_cost",
      "label_ar": "تكلفة متغيرة",
      "label_en": "variable cost",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "working_capital",
      "label_ar": "رأس المال العامل",
      "label_en": "working capital",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "owner_labor",
      "label_ar": "عمل المالك",
      "label_en": "owner labor",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "financing_cost",
      "label_ar": "تكلفة التمويل",
      "label_en": "financing cost",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "depreciation",
      "label_ar": "الاستهلاك المحاسبي",
      "label_en": "depreciation",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "contribution_margin",
      "label_ar": "هامش المساهمة",
      "label_en": "contribution margin",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "break_even_price",
      "label_ar": "سعر التعادل",
      "label_en": "break-even price",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "break_even_yield",
      "label_ar": "إنتاج التعادل",
      "label_en": "break-even yield",
      "type": "cost"
    },
    {
      "aliases": [],
      "id": "water_use",
      "label_ar": "استخدام المياه",
      "label_en": "water use",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "fertilizer_loss",
      "label_ar": "فقد الأسمدة",
      "label_en": "fertilizer loss",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "pesticide_use",
      "label_ar": "استخدام المبيدات",
      "label_en": "pesticide use",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "energy_use",
      "label_ar": "استخدام الطاقة",
      "label_en": "energy use",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "labor_impact",
      "label_ar": "أثر العمل",
      "label_en": "labor impact",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "food_loss",
      "label_ar": "فقد الغذاء",
      "label_en": "food loss",
      "type": "sustainability_impact"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "fixed_cost",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "enterprise_budget",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "variable_cost",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "enterprise_budget",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "working_capital",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "enterprise_budget",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "owner_labor",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "enterprise_budget",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "financing_cost",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "enterprise_budget",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "depreciation",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "enterprise_budget",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "contribution_margin",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "break_even_analysis",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "break_even_price",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "break_even_analysis",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "break_even_yield",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "break_even_analysis",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "enterprise_budget",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "sensitivity_analysis",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "market_suited_variety",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "buyer",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "market_information_service",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "grant_opportunity",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "competent_authority",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "export_condition",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "water_use",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "enterprise_budget",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "labor_impact",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "enterprise_budget",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "energy_use",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "enterprise_budget",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "pesticide_use",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "enterprise_budget",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "fertilizer_loss",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "enterprise_budget",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "buyer",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "cooperative",
      "type": "supports_action"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [
    "ESDU-AKKAR-VALUECHAINS",
    "ESDU-ARDI-ARDAK",
    "ESDU-FARMING-FOR-ALL"
  ],
  "supersedes_legacy_items": [
    "VALUE-CHAINS-009"
  ],
  "title_ar": "قرارات الأعمال الزراعية وسلاسل القيمة والأسواق",
  "title_en": "Farm business, value-chain, and market decisions",
  "topics": [
    "market",
    "business",
    "cost",
    "value chain"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Start with a defined customer, problem, product specification, volume, timing, alternative suppliers and evidence of willingness to buy. Production should not be planned from an assumed market alone.

Separate fixed costs, variable costs, working capital, owner labor, losses, financing and taxes or fees. Use ranges and dates for volatile inputs. Break-even quantity equals fixed costs divided by contribution per unit, where contribution is selling price minus variable cost per unit; this is an illustration, not a guarantee.

Example [ILLUSTRATIVE ONLY]: if fixed seasonal costs are USD 1,000, expected price is USD 2.00 per unit and variable cost is USD 1.20, contribution is USD 0.80 and accounting break-even is 1,250 units. The result changes with unsold or rejected product, payment delay and exchange-rate exposure.

Cooperatives may support aggregation, equipment, marketing or bargaining, but success depends on governance, member incentives, quality control, records and buyer relationships. The chatbot should not assume a cooperative is active or suitable.

Funding and export information is dynamic. The system should retrieve current official program or market requirements, show date and source and avoid implying eligibility or acceptance.

### Arabic guidance — machine draft

قد يعتمد أفضل قرار للمزارع على المشتري وسلسلة ما بعد الحصاد قبل بدء الزراعة. يجب السؤال عن السوق المستهدف ومواصفات المشتري ومرحلة النضج عند القطاف والفرز والمنتج المرفوض والتوضيب والتبريد أو التخزين ومدة النقل وخيارات التصنيع وشروط الدفع والسجلات. ينبغي التمييز بين الإنتاج الزراعي والإنتاج القابل للبيع والعائد الصافي. لا يجوز عرض فرصة سوق أو منحة مؤرخة على أنها حالية من دون مصدر مباشر وتاريخ واضح. كما تتطلب ادعاءات سلامة الغذاء والترخيص والشهادات معلومات حديثة من الجهة المختصة.

ابدأ بزبون محدد ومشكلة ومواصفة منتج وكمية وتوقيت وموردين بدلاء ودليل على الاستعداد للشراء؛ لا تخطط للإنتاج من سوق مفترض فقط.

افصل الكلفة الثابتة والمتغيرة ورأس المال العامل وعمل المالك والخسائر والتمويل والضرائب أو الرسوم، واستعمل نطاقات وتواريخ للمدخلات المتقلبة. كمية التعادل المحاسبية تساوي الكلفة الثابتة مقسومة على مساهمة الوحدة، أي سعر البيع ناقص الكلفة المتغيرة للوحدة، وهي أداة وليست ضماناً.

مثال توضيحي فقط: إذا كانت الكلفة الموسمية الثابتة 1,000 دولار، والسعر المتوقع 2.00 دولار للوحدة، والكلفة المتغيرة 1.20 دولار، فالمساهمة 0.80 دولار والتعادل 1,250 وحدة. تتغير النتيجة مع الرفض وعدم البيع وتأخر الدفع وسعر الصرف.

قد تدعم التعاونية التجميع والمعدات والتسويق أو التفاوض، لكن الفاعلية تتوقف على الحوكمة وحوافز الأعضاء وضبط الجودة والسجلات وعلاقة المشتري. التمويل والتصدير معلومات حية؛ اعرض المصدر والتاريخ ولا توحِ بالأهلية أو القبول.

### Decision logic

If local price, cost or buyer evidence is missing, provide a calculation template and sensitivity analysis rather than a profitability claim.

### منطق القرار — مسودة آلية

عند غياب سعر أو كلفة أو دليل مشترٍ محلي، قدم قالب حساب وتحليل حساسية بدلاً من ادعاء الربحية.

### Safe next action

Use a one-page assumptions sheet and update it with actual quotations, yields, rejection rates, payment terms and labor.

### الخطوة التالية الآمنة — مسودة آلية

استخدم ورقة افتراضات من صفحة واحدة وحدّثها بعروض الأسعار والمحصول الفعلي ونسبة الرفض وشروط الدفع والعمل.

### Avoid or escalate

Financial examples are not advice or guarantees. Legal and export requirements need current competent sources.

### ما يجب تجنبه أو تصعيده — مسودة آلية

الأمثلة المالية ليست نصيحة ولا ضماناً، والمتطلبات القانونية والتصديرية تحتاج مصدراً مختصاً وحديثاً.

### Evidence and applicability limits

Build current value-chain profiles for priority crops and dairy, including quality requirements, channels, seasonality and transaction constraints.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

يلزم بناء ملفات حديثة لسلاسل القيمة ذات الأولوية، ومنها المحاصيل والألبان، تشمل المواصفات والقنوات والموسمية وقيود المعاملة.

### Claim-level sources

- [ESDU-AKKAR-VALUECHAINS] Value Chains for Improved Socioeconomic Well-being of Syrian Refugees and Lebanese Host Communities — https://www.aub.edu.lb/fafs/esdu/Pages/vcproject.aspx
- [ESDU-ARDI-ARDAK] Ardi Ardak National Food Security Initiative — https://www.aub.edu.lb/fafs/esdu/Pages/ardiardakinitiative.aspx
- [ESDU-FARMING-FOR-ALL] Farming For All: Introduction to Sustainable Agriculture — https://www.aub.edu.lb/cec/Pages/Farming-For-All.aspx

## Troubleshooting without premature diagnosis / استكشاف المشكلات دون تشخيص متسرّع

```yaml
{
  "claim_ids": [
    "claim:kb-troubleshooting:guidance",
    "claim:kb-troubleshooting:decision",
    "claim:kb-troubleshooting:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "بطاطا"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "batata"
        }
      ],
      "id": "potato",
      "label_ar": "البطاطا",
      "label_en": "potato",
      "type": "crop"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "ذبول"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "zouboul"
        }
      ],
      "id": "wilting",
      "label_ar": "ذبول المحصول",
      "label_en": "crop wilting",
      "type": "symptom"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "اصفرار"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "isfirar"
        }
      ],
      "id": "yellowing",
      "label_ar": "اصفرار الأوراق",
      "label_en": "leaf yellowing",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "stunting",
      "label_ar": "تقزم النمو",
      "label_en": "stunting",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "leaf_spot",
      "label_ar": "بقع الأوراق",
      "label_en": "leaf spot",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "root_damage",
      "label_ar": "ضرر الجذور",
      "label_en": "root damage",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "diarrhea",
      "label_ar": "إسهال الحيوان",
      "label_en": "animal diarrhea",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "respiratory_distress",
      "label_ar": "ضيق التنفس",
      "label_en": "respiratory distress",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "lameness",
      "label_ar": "العرج",
      "label_en": "lameness",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "crop_disease",
      "label_ar": "مرض نباتي",
      "label_en": "crop disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "animal_disease",
      "label_ar": "مرض حيواني",
      "label_en": "animal disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "field_history",
      "label_ar": "مراجعة تاريخ الحقل",
      "label_en": "field history review",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "diagnosis_workflow",
      "label_ar": "مسار التشخيص التفريقي",
      "label_en": "differential diagnosis workflow",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "smad"
        }
      ],
      "id": "fertilizer",
      "label_ar": "سماد",
      "label_en": "fertilizer",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "salinity",
      "label_ar": "ملوحة التربة",
      "label_en": "soil salinity",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "soil_ph",
      "label_ar": "درجة حموضة التربة",
      "label_en": "soil pH",
      "type": "soil"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "EC"
        }
      ],
      "id": "soil_ec",
      "label_ar": "التوصيل الكهربائي للتربة",
      "label_en": "soil electrical conductivity",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "compaction",
      "label_ar": "انضغاط التربة",
      "label_en": "soil compaction",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "waterlogging",
      "label_ar": "تغدق التربة",
      "label_en": "waterlogging",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "root_zone_moisture",
      "label_ar": "رطوبة منطقة الجذور",
      "label_en": "root-zone moisture",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "heat",
      "label_ar": "إجهاد حراري",
      "label_en": "heat stress",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "false_diagnosis",
      "label_ar": "تشخيص متسرع",
      "label_en": "premature diagnosis",
      "type": "risk"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-ipm-safety",
      "type": "may_be_confused_with"
    },
    {
      "target": "kb-referrals",
      "type": "escalates_to"
    }
  ],
  "id": "kb-troubleshooting",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "بطاطا"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "batata"
        }
      ],
      "id": "potato",
      "label_ar": "البطاطا",
      "label_en": "potato",
      "type": "crop"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "ذبول"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "zouboul"
        }
      ],
      "id": "wilting",
      "label_ar": "ذبول المحصول",
      "label_en": "crop wilting",
      "type": "symptom"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "اصفرار"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "isfirar"
        }
      ],
      "id": "yellowing",
      "label_ar": "اصفرار الأوراق",
      "label_en": "leaf yellowing",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "stunting",
      "label_ar": "تقزم النمو",
      "label_en": "stunting",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "leaf_spot",
      "label_ar": "بقع الأوراق",
      "label_en": "leaf spot",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "root_damage",
      "label_ar": "ضرر الجذور",
      "label_en": "root damage",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "diarrhea",
      "label_ar": "إسهال الحيوان",
      "label_en": "animal diarrhea",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "respiratory_distress",
      "label_ar": "ضيق التنفس",
      "label_en": "respiratory distress",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "lameness",
      "label_ar": "العرج",
      "label_en": "lameness",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "crop_disease",
      "label_ar": "مرض نباتي",
      "label_en": "crop disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "animal_disease",
      "label_ar": "مرض حيواني",
      "label_en": "animal disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "field_history",
      "label_ar": "مراجعة تاريخ الحقل",
      "label_en": "field history review",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "diagnosis_workflow",
      "label_ar": "مسار التشخيص التفريقي",
      "label_en": "differential diagnosis workflow",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "smad"
        }
      ],
      "id": "fertilizer",
      "label_ar": "سماد",
      "label_en": "fertilizer",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "salinity",
      "label_ar": "ملوحة التربة",
      "label_en": "soil salinity",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "soil_ph",
      "label_ar": "درجة حموضة التربة",
      "label_en": "soil pH",
      "type": "soil"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "EC"
        }
      ],
      "id": "soil_ec",
      "label_ar": "التوصيل الكهربائي للتربة",
      "label_en": "soil electrical conductivity",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "compaction",
      "label_ar": "انضغاط التربة",
      "label_en": "soil compaction",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "waterlogging",
      "label_ar": "تغدق التربة",
      "label_en": "waterlogging",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "root_zone_moisture",
      "label_ar": "رطوبة منطقة الجذور",
      "label_en": "root-zone moisture",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "heat",
      "label_ar": "إجهاد حراري",
      "label_en": "heat stress",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "false_diagnosis",
      "label_ar": "تشخيص متسرع",
      "label_en": "premature diagnosis",
      "type": "risk"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "waterlogging",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "wilting",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "salinity",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "wilting",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "heat",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "wilting",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "crop_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "wilting",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "salinity",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "yellowing",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "root_damage",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "yellowing",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "crop_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "yellowing",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "compaction",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "stunting",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "insect_pest",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "leaf_spot",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "field_history",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "diagnosis_workflow",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "root_zone_moisture",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "diagnosis_workflow",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "pesticide",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "false_diagnosis",
      "type": "prohibits"
    },
    {
      "evidence_section": "English guidance",
      "object": "animal_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "diarrhea",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "animal_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "lameness",
      "type": "may_be_confused_with"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "high",
  "source_ids": [
    "ESDU-ABOUT-2026"
  ],
  "supersedes_legacy_items": [],
  "title_ar": "استكشاف المشكلات دون تشخيص متسرّع",
  "title_en": "Troubleshooting without premature diagnosis",
  "topics": [
    "symptom",
    "diagnosis",
    "observation"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Crop wilting: ask when it began, pattern, crop stage, recent weather, soil moisture at root depth, irrigation operation, root condition, salinity and recent inputs. Consider water deficit, waterlogging, root damage, salinity, heat, disease and transplant stress. Do not simply add water.

Leaf yellowing or stunting: record which leaves, pattern between veins, field distribution, roots, soil moisture, pH/EC, crop stage and input history. Nutrient deficiency is one possibility among root problems, water stress, salinity, disease, pests, herbicide injury and normal senescence. Do not prescribe fertilizer from color alone.

Leaf spots or pest damage: collect whole-plant and close images, underside, distribution, progression, weather, irrigation and signs of insects or pathogens. Isolate high-risk material where appropriate, improve sanitation and seek identification. Do not spray an unknown problem.

Livestock appetite loss or heat stress: identify species, age, number affected, duration, water/feed changes, temperature, behavior, respiration, manure and other signs. Provide shade, ventilation and clean water where safe, reduce handling and call a veterinarian for severe or multiple cases. Sudden mortality is urgent.

Product spoilage or contamination: isolate the lot, stop sale or service, preserve labels and process records, document temperature and exposure and contact a food-safety professional. Do not taste to test. Equipment malfunction: de-energize only if safe and use qualified repair; never bypass guards.

Unprofitable production: compare actual yield, grade, rejection, price, variable cost, labor, fixed cost, downtime and payment terms with the original assumptions. Avoid blaming a single input until the loss is decomposed.

### Arabic guidance — machine draft

عندما يكون السؤال عاماً، يُطرح سؤال أو سؤالان قصيران في كل مرة. تشمل المعلومات المفيدة البلدة أو الموقع، والمحصول أو الحيوان، ومرحلة النمو أو الإنتاج، وحجم الحقل أو القطيع، ومصدر المياه، والعرض الأساسي أو القرار المطلوب، والتوقيت، والهدف التسويقي. يجب قبول العربية المحكية والصوت، ثم إعادة صياغة السؤال كما فهمه النظام بلغة بسيطة كي يتمكن المزارع من تصحيحه. يُقدَّم جواب مختصر أولاً ثم التفاصيل وبطاقات المصادر. ولا يجوز أن يؤدي ضعف القراءة أو الاتصال إلى حجب معلومات السلامة الأساسية.

يساعد المساعد في اتخاذ القرار لكنه لا يحل محل المهندس الزراعي أو الطبيب البيطري أو المختبر أو مختص سلامة الغذاء أو المهندس أو الجهة الرسمية المختصة. يجب أن يتجنب وصف مواد كيميائية أو أدوية بيطرية من دون سند، أو تقديم ضمانات قانونية، أو إعطاء تشخيص مؤكد انطلاقاً من نص أو صورة محدودة. تُحال الحالات العاجلة مثل مرض الحيوان الشديد أو الاشتباه بالتسمم أو تعرض العامل لمادة خطرة أو تلوث الغذاء أو المياه أو الخسارة السريعة الانتشار في المحصول أو الأخطار الإنشائية والكهربائية وأي خطر فوري. ويُطلب الحد الأدنى من المعلومات المفيدة من دون جمع بيانات شخصية غير ضرورية.

عند ذبول المحصول، اسأل عن البداية والنمط والمرحلة والطقس ورطوبة عمق الجذر وتشغيل الري والجذور والملوحة والمدخلات. تشمل الاحتمالات نقص الماء وزيادته والتغدق وتلف الجذور والملوحة والحر والمرض وصدمة الشتل؛ لا تضف الماء تلقائياً.

عند الاصفرار أو التقزم، سجّل الأوراق المصابة والنمط بين العروق وتوزع الحقل والجذور والرطوبة والحموضة والموصلية والمرحلة والمدخلات. نقص العنصر احتمال إلى جانب مشكلات الجذر والماء والملوحة والمرض والآفات وأذى مبيد الأعشاب والشيخوخة؛ لا تصف السماد من اللون.

لبقع الأوراق أو ضرر الآفة، اجمع صورة النبات كاملاً والتفاصيل وأسفل الورقة والتوزع والتقدم والطقس والري وعلامات الحشرات أو الممرض. اعزل المادة عالية الخطر عند الملاءمة وحسّن النظافة واطلب التعريف؛ لا ترش مشكلة مجهولة.

لنقص شهية الحيوان أو الحر، حدّد النوع والعمر والعدد والمدة وتغير الماء والعلف والحرارة والسلوك والتنفس والروث وباقي العلامات. وفّر ماء نظيفاً وظلاً وتهوية حيث يكون ذلك آمناً وقلل المناولة، واتصل بطبيب عند الحالات الشديدة أو المتعددة. النفوق المفاجئ عاجل.

عند فساد أو تلوث منتج، اعزل الدفعة وأوقف البيع أو التقديم واحفظ الملصق وسجل العملية ووثق الحرارة والتعرض واتصل بمختص؛ لا تتذوق. وعند عطل معدة افصل الطاقة فقط إذا كان ذلك آمناً واستعمل فنياً ولا تتجاوز الحواجز.

لفهم خسارة الإنتاج، قارن المحصول والدرجة والرفض والسعر والكلفة المتغيرة والعمل والثابت والتوقف وشروط الدفع بالافتراضات، ولا تلُم مدخلاً واحداً قبل تفكيك الخسارة.

### Decision logic

Ask whether any human, animal, food or chemical emergency is present before routine troubleshooting. Escalation overrides completion of the questionnaire.

### منطق القرار — مسودة آلية

اسأل أولاً عن طارئ بشري أو حيواني أو غذائي أو كيميائي؛ التصعيد يسبق استكمال شجرة الأسئلة.

### Safe next action

Each pathway should produce a structured case record that an expert can review, not a definitive diagnosis.

### الخطوة التالية الآمنة — مسودة آلية

ينتج كل مسار سجل حالة منظماً يمكن للخبير مراجعته، لا تشخيصاً نهائياً.

### Avoid or escalate

Never treat a diagnostic tree as proof. It narrows questions and supports referral.

### ما يجب تجنبه أو تصعيده — مسودة آلية

شجرة التشخيص ليست إثباتاً؛ وظيفتها تضييق الأسئلة ودعم الإحالة.

### Evidence and applicability limits

Add expert-approved local look-alikes, referral routes and typical equipment configurations after field validation.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

تضاف المتشابهات المحلية ومسارات الإحالة وتجهيزات المعدات الشائعة بعد اعتماد الخبراء والتحقق الحقلي.

### Claim-level sources

- [ESDU-ABOUT-2026] About ESDU — https://aub.edu.lb/fafs/esdu/Pages/About-ESDU.aspx

## Recommendation and decision rules / قواعد التوصية واتخاذ القرار

```yaml
{
  "claim_ids": [
    "claim:kb-decision-rules:guidance",
    "claim:kb-decision-rules:decision",
    "claim:kb-decision-rules:safety"
  ],
  "content_kind": "workflow",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [],
      "id": "diagnosis_workflow",
      "label_ar": "مسار التشخيص التفريقي",
      "label_en": "differential diagnosis workflow",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "professional_referral",
      "label_ar": "الإحالة المهنية",
      "label_en": "professional referral",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "product_label",
      "label_ar": "ملصق المنتج المسجل",
      "label_en": "registered product label",
      "type": "regulation"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-scope-local-context",
      "type": "requires_context"
    }
  ],
  "id": "kb-decision-rules",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [],
      "id": "diagnosis_workflow",
      "label_ar": "مسار التشخيص التفريقي",
      "label_en": "differential diagnosis workflow",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "professional_referral",
      "label_ar": "الإحالة المهنية",
      "label_en": "professional referral",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "product_label",
      "label_ar": "ملصق المنتج المسجل",
      "label_en": "registered product label",
      "type": "regulation"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "site_assessment",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "diagnosis_workflow",
      "type": "depends_on"
    },
    {
      "evidence_section": "English guidance",
      "object": "product_label",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "pesticide",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "false_diagnosis",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "professional_referral",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "market_information_service",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "stale_information",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "agronomist",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "diagnosis_workflow",
      "type": "requires_context"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [
    "ESDU-ABOUT-2026"
  ],
  "supersedes_legacy_items": [],
  "title_ar": "قواعد التوصية واتخاذ القرار",
  "title_en": "Recommendation and decision rules",
  "topics": [
    "practice",
    "decision rules",
    "context",
    "uncertainty"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Rule 1—identify intent: information, diagnosis support, action selection, rate, emergency, service, price or law. Rule 2—classify risk. Rule 3—check whether the answer is time-sensitive. Rule 4—retrieve sources approved for that intent and risk. Rule 5—check context sufficiency and local applicability. Rule 6—answer, ask, narrow, refuse or escalate.

Minimum sufficiency is task-specific. A pesticide rate requires product, active ingredient, formulation, label, crop, target, jurisdiction and application context—and remains subject to expert policy. An irrigation schedule requires crop, stage, soil, area, system flow and weather. A veterinary medication request is outside chatbot prescribing scope.

When multiple causes remain plausible, list them as hypotheses, explain evidence that separates them and recommend low-risk immediate actions. Do not rank a cause confidently merely because it is common globally.

When sources conflict, explain the disagreement and why it matters. If the conflict affects safety or legality, do not choose; escalate. When a current source is unavailable, disclose the outage and avoid stale assertions.

Advice should separate: what is known; what is assumed; what the user should observe; safe immediate action; what to avoid; when to refer; and sources. This structure supports both human trust and evaluation.

### Arabic guidance — machine draft

عندما يكون السؤال عاماً، يُطرح سؤال أو سؤالان قصيران في كل مرة. تشمل المعلومات المفيدة البلدة أو الموقع، والمحصول أو الحيوان، ومرحلة النمو أو الإنتاج، وحجم الحقل أو القطيع، ومصدر المياه، والعرض الأساسي أو القرار المطلوب، والتوقيت، والهدف التسويقي. يجب قبول العربية المحكية والصوت، ثم إعادة صياغة السؤال كما فهمه النظام بلغة بسيطة كي يتمكن المزارع من تصحيحه. يُقدَّم جواب مختصر أولاً ثم التفاصيل وبطاقات المصادر. ولا يجوز أن يؤدي ضعف القراءة أو الاتصال إلى حجب معلومات السلامة الأساسية.

يساعد المساعد في اتخاذ القرار لكنه لا يحل محل المهندس الزراعي أو الطبيب البيطري أو المختبر أو مختص سلامة الغذاء أو المهندس أو الجهة الرسمية المختصة. يجب أن يتجنب وصف مواد كيميائية أو أدوية بيطرية من دون سند، أو تقديم ضمانات قانونية، أو إعطاء تشخيص مؤكد انطلاقاً من نص أو صورة محدودة. تُحال الحالات العاجلة مثل مرض الحيوان الشديد أو الاشتباه بالتسمم أو تعرض العامل لمادة خطرة أو تلوث الغذاء أو المياه أو الخسارة السريعة الانتشار في المحصول أو الأخطار الإنشائية والكهربائية وأي خطر فوري. ويُطلب الحد الأدنى من المعلومات المفيدة من دون جمع بيانات شخصية غير ضرورية.

القاعدة 1: حدّد القصد—معلومة أو دعم تشخيص أو اختيار فعل أو جرعة أو طارئ أو خدمة أو سعر أو قانون. القاعدة 2: صنّف الخطر. القاعدة 3: حدّد حساسية الزمن. القاعدة 4: استرجع مصادر معتمدة للقصد والخطر. القاعدة 5: افحص كفاية السياق والملاءمة المحلية. القاعدة 6: أجب أو اسأل أو ضيّق أو ارفض أو صعّد.

الكفاية تختلف حسب المهمة. جرعة مبيد تحتاج المنتج والمادة الفعالة والتركيبة والملصق والمحصول والهدف والاختصاص والسياق، وتظل خاضعة لسياسة الخبير. برنامج الري يحتاج المحصول والمرحلة والتربة والمساحة وتدفق الشبكة والطقس. طلب دواء بيطري خارج نطاق وصف المساعد.

عند بقاء أسباب متعددة، اعرضها كفرضيات واشرح الدليل الفاصل واقترح أفعالاً فورية منخفضة الخطر، ولا ترفع سبباً لأنه شائع عالمياً. عند تعارض المصادر اشرح الخلاف وأثره؛ وإذا مس السلامة أو القانون فلا تختَر وصعّد. وإذا غاب المصدر الحالي صرّح بالتعطل ولا تستعمل ادعاء قديماً.

افصل في الجواب ما هو معروف وما هو مفترض وما يجب ملاحظته والفعل الآمن وما يجب تجنبه ومتى تكون الإحالة والمصادر.

### Decision logic

If evidence or context is insufficient, state the gap and do not infer a precise recommendation.

### منطق القرار — مسودة آلية

إذا كان الدليل أو السياق غير كافٍ، اذكر الفجوة ولا تستنتج توصية دقيقة.

### Safe next action

Implement rules as testable policy functions and log the decision path, retrieved chunks, answer and user feedback without collecting unnecessary personal data.

### الخطوة التالية الآمنة — مسودة آلية

حوّل القواعد إلى وظائف سياسة قابلة للاختبار، وسجّل مسار القرار والمقاطع المسترجعة والجواب والتغذية الراجعة من دون بيانات شخصية غير لازمة.

### Avoid or escalate

No confidence score should override a hard prohibition, legal requirement or critical escalation rule.

### ما يجب تجنبه أو تصعيده — مسودة آلية

لا تتغلب درجة الثقة على منع صريح أو متطلب قانوني أو قاعدة تصعيد حرجة.

### Evidence and applicability limits

Apply these decision rules only within the declared geography, production system, season, evidence scope, and channel policy.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

تطبق القواعد ضمن المكان ونظام الإنتاج والموسم وحدود الأدلة المعلنة.

### Claim-level sources

- [ESDU-ABOUT-2026] About ESDU — https://aub.edu.lb/fafs/esdu/Pages/About-ESDU.aspx

## Frequently asked farm questions / الأسئلة الزراعية الشائعة

```yaml
{
  "claim_ids": [
    "claim:kb-faq:guidance",
    "claim:kb-faq:decision",
    "claim:kb-faq:safety"
  ],
  "content_kind": "workflow",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "بطاطا"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "batata"
        }
      ],
      "id": "potato",
      "label_ar": "البطاطا",
      "label_en": "potato",
      "type": "crop"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "ذبول"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "zouboul"
        }
      ],
      "id": "wilting",
      "label_ar": "ذبول المحصول",
      "label_en": "crop wilting",
      "type": "symptom"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "اصفرار"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "isfirar"
        }
      ],
      "id": "yellowing",
      "label_ar": "اصفرار الأوراق",
      "label_en": "leaf yellowing",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "weed",
      "label_ar": "عشب ضار",
      "label_en": "weed",
      "type": "pest"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "jadwalet el ray"
        }
      ],
      "id": "irrigation_scheduling",
      "label_ar": "جدولة الري",
      "label_en": "irrigation scheduling",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "smad"
        }
      ],
      "id": "fertilizer",
      "label_ar": "سماد",
      "label_en": "fertilizer",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "glyphosate",
      "label_ar": "غليفوسات",
      "label_en": "glyphosate",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "emitter_flow",
      "label_ar": "تصريف النقاط",
      "label_en": "emitter flow",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "root_zone_moisture",
      "label_ar": "رطوبة منطقة الجذور",
      "label_en": "root-zone moisture",
      "type": "water"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-decision-rules",
      "type": "related_to"
    }
  ],
  "id": "kb-faq",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "بطاطا"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "batata"
        }
      ],
      "id": "potato",
      "label_ar": "البطاطا",
      "label_en": "potato",
      "type": "crop"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "ذبول"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "zouboul"
        }
      ],
      "id": "wilting",
      "label_ar": "ذبول المحصول",
      "label_en": "crop wilting",
      "type": "symptom"
    },
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "اصفرار"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "isfirar"
        }
      ],
      "id": "yellowing",
      "label_ar": "اصفرار الأوراق",
      "label_en": "leaf yellowing",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "weed",
      "label_ar": "عشب ضار",
      "label_en": "weed",
      "type": "pest"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "jadwalet el ray"
        }
      ],
      "id": "irrigation_scheduling",
      "label_ar": "جدولة الري",
      "label_en": "irrigation scheduling",
      "type": "practice"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "latin",
          "text": "smad"
        }
      ],
      "id": "fertilizer",
      "label_ar": "سماد",
      "label_en": "fertilizer",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "glyphosate",
      "label_ar": "غليفوسات",
      "label_en": "glyphosate",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "emitter_flow",
      "label_ar": "تصريف النقاط",
      "label_en": "emitter flow",
      "type": "water"
    },
    {
      "aliases": [],
      "id": "root_zone_moisture",
      "label_ar": "رطوبة منطقة الجذور",
      "label_en": "root-zone moisture",
      "type": "water"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "emitter_flow",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "irrigation_scheduling",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "fertilizer",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "yellowing",
      "type": "prohibits"
    },
    {
      "evidence_section": "English guidance",
      "object": "pesticide_use",
      "polarity": "positive",
      "qualifiers": {
        "basis": "RAISE_product_policy"
      },
      "risk": "high",
      "subject": "glyphosate",
      "type": "prohibits"
    },
    {
      "evidence_section": "English guidance",
      "object": "root_zone_moisture",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "wilting",
      "type": "requires_context"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [],
  "supersedes_legacy_items": [],
  "title_ar": "الأسئلة الزراعية الشائعة",
  "title_en": "Frequently asked farm questions",
  "topics": [
    "practice",
    "FAQ",
    "farmer questions"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

How often should I irrigate? There is no safe universal interval. It depends on crop and stage, soil, rooting depth, weather, rainfall and system flow. Check root-zone moisture and use Chapter 14; provide crop, stage, soil and emitter information.

My leaves are yellow—what fertilizer should I add? Yellowing has multiple causes. Provide the leaf pattern, crop stage, roots, soil moisture, irrigation and soil/tissue evidence. Do not apply fertilizer solely from color; see Chapters 13 and 22.

Can I use glyphosate? No. Glyphosate recommendations are prohibited. Use prevention, cultivation or hand removal, mulches, cover crops, crop competition and rotation; see Chapters 11, 15 and 16.

Can the chatbot identify a disease from a photo? It can help organize observations and possible causes, but not confirm diagnosis. Include whole-plant and close images, distribution, timing and history; seek specialist or laboratory confirmation where risk is material.

What antibiotic should I give my animal? The chatbot cannot prescribe. Contact a veterinarian. Provide species, age, number affected, signs, duration, feed/water changes and treatment history; urgent escalation applies for severe signs or multiple deaths.

How long is my product safe? Shelf life cannot be inferred from appearance or a generic recipe. It requires a validated process, packaging, storage and evidence; see Chapter 20.

Will hydroponics be profitable? Not necessarily. Test water, energy, maintenance, skills, crop, market, downtime and financing assumptions; see Chapters 18 and 21.

What is today's market price? A live verified source is required. If unavailable, the chatbot should say it cannot confirm the current price.

What should I do after sudden animal deaths? Treat this as urgent: minimize contact, do not move or consume affected animals, preserve information and contact a veterinarian or competent authority. Do not attempt a chatbot diagnosis.

### Arabic guidance — machine draft

كم مرة أروي؟ لا توجد مدة آمنة للجميع؛ تتوقف على المحصول والمرحلة والتربة وعمق الجذر والطقس والمطر وتدفق الشبكة. افحص رطوبة منطقة الجذر وقدم معلومات المحصول والمرحلة والتربة والنقاطات.

أوراقي صفراء، أي سماد أضيف؟ للاصفرار أسباب متعددة. قدّم نمط الورقة والمرحلة والجذور والرطوبة والري ودليل التربة أو الأنسجة. لا تسمّد اعتماداً على اللون.

هل أستعمل الغليفوسات؟ لا تقدم RAISE توصيات لاستخدامه. استخدم الوقاية والعزيق أو الإزالة اليدوية والملش ومحاصيل التغطية والتنافس والدورة.

هل يشخّص المساعد المرض من صورة؟ يساعد في تنظيم الملاحظات والأسباب المحتملة، ولا يثبت التشخيص. أرفق النبات كاملاً والتفاصيل والتوزع والتوقيت والتاريخ واطلب خبيراً أو مختبراً عند الخطر.

أي مضاد حيوي أعطي الحيوان؟ لا يصف المساعد. اتصل بطبيب وقدم النوع والعمر والعدد والعلامات والمدة وتغير العلف والماء والعلاج السابق؛ الحالات الشديدة أو النفوق المتعدد عاجلة.

كم يبقى المنتج آمناً؟ لا تُستنتج الصلاحية من الشكل أو وصفة عامة؛ تحتاج عملية موثقة وتعبئة وتخزيناً ودليلاً.

هل الزراعة المائية مربحة؟ ليس بالضرورة. اختبر الماء والطاقة والصيانة والمهارة والمحصول والسوق والتوقف والتمويل.

ما سعر السوق اليوم؟ يلزم مصدر حي موثوق؛ إذا غاب يجب القول إن السعر الحالي غير مؤكد.

ماذا أفعل بعد نفوق مفاجئ؟ قلل الملامسة، ولا تنقل أو تستهلك الحيوان المتأثر، واحفظ المعلومات واتصل بطبيب أو سلطة؛ لا تحاول تشخيصاً آلياً.

### Decision logic

When an FAQ omits necessary context, ask the minimum follow-up question or escalate rather than expanding into a generic answer.

### منطق القرار — مسودة آلية

إذا حذف السؤال الشائع سياقاً ضرورياً، اطرح أقل سؤال متابعة أو صعّد بدلاً من توسيع جواب عام.

### Safe next action

FAQ answers should stay short and link to the approved detailed pathway. They should not become separate ungoverned copies.

### الخطوة التالية الآمنة — مسودة آلية

أبقِ الجواب قصيراً واربطه بالمسار التفصيلي المعتمد؛ لا تنشئ نسخة معرفة غير محكومة.

### Avoid or escalate

FAQ brevity must not remove a critical warning, refusal or referral.

### ما يجب تجنبه أو تصعيده — مسودة آلية

لا يجوز أن يحذف الاختصار تحذيراً أو رفضاً أو إحالة حرجة.

### Evidence and applicability limits

Collect actual user questions in Arabic and English, then update wording and priority with approval.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

تُجمع أسئلة المستخدمين الفعلية بالعربية والإنجليزية، ثم تُحدّث الصياغة والأولوية بعد الاعتماد.

### Claim-level sources


## Common agrifood misconceptions / مفاهيم زراعية وغذائية شائعة وخاطئة

```yaml
{
  "claim_ids": [
    "claim:kb-misconceptions:guidance",
    "claim:kb-misconceptions:decision",
    "claim:kb-misconceptions:safety"
  ],
  "content_kind": "evidence",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [
    {
      "aliases": [],
      "id": "soil_health",
      "label_ar": "صحة التربة",
      "label_en": "soil health",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "organic_standard",
      "label_ar": "معيار الإنتاج العضوي",
      "label_en": "organic production standard",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "false_diagnosis",
      "label_ar": "تشخيص متسرع",
      "label_en": "premature diagnosis",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "water_use",
      "label_ar": "استخدام المياه",
      "label_en": "water use",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "fertilizer_loss",
      "label_ar": "فقد الأسمدة",
      "label_en": "fertilizer loss",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "biodiversity",
      "label_ar": "التنوع الحيوي الزراعي",
      "label_en": "farm biodiversity",
      "type": "sustainability_impact"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-decision-rules",
      "type": "conflicts_with"
    }
  ],
  "id": "kb-misconceptions",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [],
      "id": "soil_health",
      "label_ar": "صحة التربة",
      "label_en": "soil health",
      "type": "soil"
    },
    {
      "aliases": [],
      "id": "organic_standard",
      "label_ar": "معيار الإنتاج العضوي",
      "label_en": "organic production standard",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "false_diagnosis",
      "label_ar": "تشخيص متسرع",
      "label_en": "premature diagnosis",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "water_use",
      "label_ar": "استخدام المياه",
      "label_en": "water use",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "fertilizer_loss",
      "label_ar": "فقد الأسمدة",
      "label_en": "fertilizer loss",
      "type": "sustainability_impact"
    },
    {
      "aliases": [],
      "id": "biodiversity",
      "label_ar": "التنوع الحيوي الزراعي",
      "label_en": "farm biodiversity",
      "type": "sustainability_impact"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "fertilizer_loss",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "irrigation_water",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "fertilizer_loss",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "fertilizer",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "pesticide_use",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "false_diagnosis",
      "type": "may_cause"
    },
    {
      "evidence_section": "English guidance",
      "object": "competent_authority",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "organic_standard",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "biodiversity",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "ipm",
      "type": "supports_action"
    },
    {
      "evidence_section": "English guidance",
      "object": "root_damage",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "waterlogging",
      "type": "may_cause"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [
    "WOAH-ANTIMICROBIAL-USE-2024"
  ],
  "supersedes_legacy_items": [],
  "title_ar": "مفاهيم زراعية وغذائية شائعة وخاطئة",
  "title_en": "Common agrifood misconceptions",
  "topics": [
    "risk",
    "misconceptions",
    "evidence"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

More water or fertilizer does not always increase yield. Excess water can reduce root oxygen and move nutrients; excess fertilizer can increase salt stress, imbalance, cost and environmental loss. Evidence from soil, crop and irrigation should guide adjustment.

A photo or sensor reading is not a complete diagnosis. Similar symptoms can arise from different causes; sensors drift, sample only part of a system and may fail. Cross-check against context and independent observations.

'Natural' does not mean safe, and 'organic' does not mean free of hazards. Biological products, manure, plant extracts and homemade mixtures may harm people, crops, animals or ecosystems. Food hygiene and legal requirements still apply.

Antibiotics do not treat every animal illness and misuse contributes to resistance and residue risk. Veterinary oversight, prevention, diagnosis and records are required [source: WOAH-ANTIMICROBIAL-USE-2024].

Hydroponics is not automatically low-cost or profitable. It shifts requirements toward water quality, nutrients, pumps, monitoring, energy, maintenance and markets.

A cooperative is not automatically an effective market solution. Governance, quality, member incentives, records and buyer relationships determine function.

An AI answer with a citation can still be wrong if the citation does not support the claim, is outdated or does not fit the location. Retrieval and answer faithfulness must be evaluated separately.

### Arabic guidance — machine draft

الماء أو السماد الأكثر لا يضمن محصولاً أعلى. زيادة الماء تقلل أكسجين الجذور وقد تحرك العناصر، وزيادة السماد قد ترفع الملوحة والاختلال والكلفة والفقد البيئي. يقود التعديل دليل التربة والنبات والري.

الصورة أو قراءة الحساس ليست تشخيصاً كاملاً. تتشابه الأعراض وقد ينحرف الحساس أو يمثل جزءاً صغيراً أو يتعطل؛ قارن بالسياق وقياس مستقل.

«طبيعي» لا يعني آمناً و«عضوي» لا يعني خالياً من الخطر. قد تؤذي المنتجات الحيوية والسماد البلدي والمستخلصات والخلطات المنزلية الناس أو النبات أو الحيوان أو البيئة، وتبقى النظافة والقانون لازمين.

المضاد الحيوي لا يعالج كل مرض حيواني، وسوء استعماله يزيد المقاومة وبقايا الدواء. يلزم إشراف بيطري ووقاية وتشخيص وسجلات [source: WOAH-ANTIMICROBIAL-USE-2024].

الزراعة المائية ليست تلقائياً رخيصة أو مربحة؛ تنقل المتطلبات إلى الماء والعناصر والمضخات والرصد والطاقة والصيانة والسوق. والتعاونية ليست حلاً تلقائياً؛ تحدد الحوكمة والجودة والحوافز والسجلات والمشترون فاعليتها.

قد يكون جواب الذكاء الاصطناعي ذا استشهاد وخاطئاً إذا لم يدعم المصدر الادعاء أو كان قديماً أو غير ملائم للمكان؛ تُقيّم جودة الاسترجاع ووفاء الجواب منفصلين.

### Decision logic

When evidence or context is insufficient to correct a claim, state the gap and do not infer a precise recommendation.

### منطق القرار — مسودة آلية

إذا كان الدليل أو السياق ناقصاً، اذكر الفجوة ولا تستنتج توصية دقيقة.

### Safe next action

Use misconception cards with 'claim', 'why incomplete', 'what evidence matters', 'safe next step' and 'source'.

### الخطوة التالية الآمنة — مسودة آلية

استخدم بطاقة «الادعاء، لماذا هو ناقص، ما الدليل المهم، الخطوة الآمنة، المصدر».

### Avoid or escalate

Correct misinformation respectfully and avoid ridicule. High-risk misinformation should trigger direct, clear warnings.

### ما يجب تجنبه أو تصعيده — مسودة آلية

صحح باحترام ومن دون سخرية، واجعل التضليل عالي الخطر يطلق تحذيراً واضحاً ومباشراً.

### Evidence and applicability limits

Collect misconceptions through anonymized queries, workshops and expert interviews, then validate frequency and risk.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

تجمع المفاهيم الخاطئة من استفسارات مجهّلة وورش ومقابلات خبراء، ثم يُتحقق من شيوعها وخطرها.

### Claim-level sources

- [WOAH-ANTIMICROBIAL-USE-2024] WOAH. Responsible and prudent use of antimicrobial agents in veterinary medicine, Chapter 6.10. 2024. — https://www.woah.org/fileadmin/Home/eng/Health_standards/tahc/2023/chapitre_antibio_use.pdf

## Useful referral and escalation hand-offs / الإحالات والتصعيد العملي المفيد

```yaml
{
  "claim_ids": [
    "claim:kb-referrals:guidance",
    "claim:kb-referrals:decision",
    "claim:kb-referrals:safety"
  ],
  "content_kind": "workflow",
  "dynamicity": "live_only",
  "effective_from": null,
  "entities": [
    {
      "aliases": [],
      "id": "rural_lebanon",
      "label_ar": "لبنان الريفي",
      "label_en": "rural Lebanon",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "sudden_mortality",
      "label_ar": "نفوق مفاجئ",
      "label_en": "sudden mortality",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "zoonotic_disease",
      "label_ar": "مرض حيواني المنشأ",
      "label_en": "zoonotic disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "foodborne_disease",
      "label_ar": "مرض منقول بالغذاء",
      "label_en": "foodborne disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "isolation",
      "label_ar": "عزل الخطر",
      "label_en": "risk isolation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "professional_referral",
      "label_ar": "الإحالة المهنية",
      "label_en": "professional referral",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "competent_authority",
      "label_ar": "السلطة المختصة",
      "label_en": "competent authority",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "cooperative",
      "label_ar": "تعاونية زراعية",
      "label_en": "farmer cooperative",
      "type": "organization"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مهندس زراعي"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mhandes zira3e"
        }
      ],
      "id": "agronomist",
      "label_ar": "مهندس زراعي مؤهل",
      "label_en": "qualified agronomist",
      "type": "service"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "دكتور بيطري"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "doctor baytari"
        }
      ],
      "id": "veterinarian",
      "label_ar": "طبيب بيطري",
      "label_en": "veterinarian",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "soil_water_lab",
      "label_ar": "مختبر تربة ومياه",
      "label_en": "soil and water laboratory",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "food_safety_specialist",
      "label_ar": "اختصاصي سلامة غذاء",
      "label_en": "food-safety specialist",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "irrigation_engineer",
      "label_ar": "مهندس ري",
      "label_en": "irrigation engineer",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "emergency_service",
      "label_ar": "خدمة طوارئ",
      "label_en": "emergency service",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "extension_service",
      "label_ar": "خدمة الإرشاد الزراعي",
      "label_en": "agricultural extension service",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "poisoning",
      "label_ar": "اشتباه تسمم",
      "label_en": "suspected poisoning",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "worker_exposure",
      "label_ar": "تعرض العامل لمادة كيميائية",
      "label_en": "worker chemical exposure",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "food_contamination",
      "label_ar": "تلوث الغذاء",
      "label_en": "food contamination",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "zoonotic_exposure",
      "label_ar": "تعرض لمرض حيواني المنشأ",
      "label_en": "zoonotic exposure",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "electrical_danger",
      "label_ar": "خطر آلي أو كهربائي",
      "label_en": "machinery or electrical danger",
      "type": "risk"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-dynamic-information",
      "type": "requires_live_source"
    }
  ],
  "id": "kb-referrals",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [],
      "id": "rural_lebanon",
      "label_ar": "لبنان الريفي",
      "label_en": "rural Lebanon",
      "type": "location"
    },
    {
      "aliases": [],
      "id": "sudden_mortality",
      "label_ar": "نفوق مفاجئ",
      "label_en": "sudden mortality",
      "type": "symptom"
    },
    {
      "aliases": [],
      "id": "zoonotic_disease",
      "label_ar": "مرض حيواني المنشأ",
      "label_en": "zoonotic disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "foodborne_disease",
      "label_ar": "مرض منقول بالغذاء",
      "label_en": "foodborne disease",
      "type": "disease"
    },
    {
      "aliases": [],
      "id": "isolation",
      "label_ar": "عزل الخطر",
      "label_en": "risk isolation",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "professional_referral",
      "label_ar": "الإحالة المهنية",
      "label_en": "professional referral",
      "type": "practice"
    },
    {
      "aliases": [],
      "id": "competent_authority",
      "label_ar": "السلطة المختصة",
      "label_en": "competent authority",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "cooperative",
      "label_ar": "تعاونية زراعية",
      "label_en": "farmer cooperative",
      "type": "organization"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "مهندس زراعي"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mhandes zira3e"
        }
      ],
      "id": "agronomist",
      "label_ar": "مهندس زراعي مؤهل",
      "label_en": "qualified agronomist",
      "type": "service"
    },
    {
      "aliases": [
        {
          "language": "arz",
          "script": "arabic",
          "text": "دكتور بيطري"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "doctor baytari"
        }
      ],
      "id": "veterinarian",
      "label_ar": "طبيب بيطري",
      "label_en": "veterinarian",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "soil_water_lab",
      "label_ar": "مختبر تربة ومياه",
      "label_en": "soil and water laboratory",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "food_safety_specialist",
      "label_ar": "اختصاصي سلامة غذاء",
      "label_en": "food-safety specialist",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "irrigation_engineer",
      "label_ar": "مهندس ري",
      "label_en": "irrigation engineer",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "emergency_service",
      "label_ar": "خدمة طوارئ",
      "label_en": "emergency service",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "extension_service",
      "label_ar": "خدمة الإرشاد الزراعي",
      "label_en": "agricultural extension service",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "poisoning",
      "label_ar": "اشتباه تسمم",
      "label_en": "suspected poisoning",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "worker_exposure",
      "label_ar": "تعرض العامل لمادة كيميائية",
      "label_en": "worker chemical exposure",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "food_contamination",
      "label_ar": "تلوث الغذاء",
      "label_en": "food contamination",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "zoonotic_exposure",
      "label_ar": "تعرض لمرض حيواني المنشأ",
      "label_en": "zoonotic exposure",
      "type": "risk"
    },
    {
      "aliases": [],
      "id": "electrical_danger",
      "label_ar": "خطر آلي أو كهربائي",
      "label_en": "machinery or electrical danger",
      "type": "risk"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "emergency_service",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "critical",
      "subject": "poisoning",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "veterinarian",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "critical",
      "subject": "zoonotic_exposure",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "competent_authority",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "critical",
      "subject": "sudden_mortality",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "food_safety_specialist",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "food_contamination",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "agronomist",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "root_damage",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "soil_water_lab",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "salinity",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "soil_water_lab",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "water_quality",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "irrigation_engineer",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "irrigation_scheduling",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "emergency_service",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "critical",
      "subject": "electrical_danger",
      "type": "escalates_to"
    },
    {
      "evidence_section": "English guidance",
      "object": "extension_service",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "professional_referral",
      "type": "requires_context"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [
    "MOA-EXTENSION-CENTERS"
  ],
  "supersedes_legacy_items": [
    "EXTENSION-REFERRAL-021"
  ],
  "title_ar": "الإحالات والتصعيد العملي المفيد",
  "title_en": "Useful referral and escalation hand-offs",
  "topics": [
    "service",
    "referral",
    "extension",
    "expert"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

A referral should be specific enough to help the user act: problem category, urgency, region, service type, what evidence to bring, eligibility or cost if confirmed, current contact method, hours, verification date and source.

Critical categories include suspected poisoning, human injury, zoonotic exposure, severe animal illness, sudden mortality, serious foodborne illness, major contamination and immediate machinery or electrical danger. The chatbot should direct the user to competent emergency or professional services and avoid delaying action with a long questionnaire.

Technical referrals include agronomist, crop specialist, soil or water laboratory, plant pathologist, entomologist, irrigation engineer, veterinarian, food-safety specialist, processor or business advisor. The referral record must state whether the service is diagnostic, advisory, regulatory or emergency.

Directory fields: organization, service, region, language, contact method, hours, cost, eligibility, documents, emergency status, date verified, owner, source and fallback. Expired records should not be retrieved as current.

### Arabic guidance — machine draft

يساعد المساعد في اتخاذ القرار لكنه لا يحل محل المهندس الزراعي أو الطبيب البيطري أو المختبر أو مختص سلامة الغذاء أو المهندس أو الجهة الرسمية المختصة. يجب أن يتجنب وصف مواد كيميائية أو أدوية بيطرية من دون سند، أو تقديم ضمانات قانونية، أو إعطاء تشخيص مؤكد انطلاقاً من نص أو صورة محدودة. تُحال الحالات العاجلة مثل مرض الحيوان الشديد أو الاشتباه بالتسمم أو تعرض العامل لمادة خطرة أو تلوث الغذاء أو المياه أو الخسارة السريعة الانتشار في المحصول أو الأخطار الإنشائية والكهربائية وأي خطر فوري. ويُطلب الحد الأدنى من المعلومات المفيدة من دون جمع بيانات شخصية غير ضرورية.

تكون الإحالة قابلة للتنفيذ عندما تذكر فئة المشكلة والاستعجال والمنطقة ونوع الخدمة وما يحمله المستخدم من أدلة، والأهلية أو الكلفة إذا تأكدتا، وطريقة الاتصال الحالية والدوام وتاريخ التحقق والمصدر.

تشمل الحالات الحرجة تسمماً محتملاً أو إصابة بشرية أو تعرضاً لمرض مشترك أو مرضاً حيوانياً شديداً أو نفوقاً مفاجئاً أو مرضاً غذائياً خطيراً أو تلوثاً كبيراً أو خطراً فورياً من آلة أو كهرباء. وجّه إلى طوارئ أو مهني مختص ولا تؤخره باستبيان طويل.

تشمل الإحالات الفنية مهندساً زراعياً أو اختصاصي محصول أو مختبر تربة وماء أو أمراض نبات أو حشرات أو مهندس ري أو طبيباً بيطرياً أو اختصاصي سلامة غذاء أو تصنيع أو أعمال. يوضح السجل هل الخدمة تشخيصية أو استشارية أو تنظيمية أو طارئة.

حقول الدليل: المنظمة والخدمة والمنطقة واللغة وطريقة الاتصال والدوام والكلفة والأهلية والوثائق وحالة الطوارئ وتاريخ التحقق والمالك والمصدر والبديل. لا تُسترجع السجلات المنتهية كأنها حالية.

### Decision logic

If no verified local contact is available, state that clearly and identify the type of professional or authority needed without inventing details.

### منطق القرار — مسودة آلية

إذا لم يوجد اتصال محلي موثّق، قل ذلك وحدد نوع المهني أو السلطة المطلوبة من دون اختراع تفاصيل.

### Safe next action

Assign an owner to verify high-use records monthly or quarterly depending on volatility, and immediately after reported failure.

### الخطوة التالية الآمنة — مسودة آلية

عيّن مسؤولاً يراجع السجلات كثيرة الاستخدام شهرياً أو فصلياً بحسب تغيرها، وفور الإبلاغ عن فشلها.

### Avoid or escalate

Do not publish personal mobile numbers without authorization. Do not route emergencies to an unverified social account.

### ما يجب تجنبه أو تصعيده — مسودة آلية

لا تنشر رقماً خلوياً شخصياً بلا إذن، ولا تحل طارئاً إلى حساب اجتماعي غير موثّق.

### Evidence and applicability limits

Build and consent-check the Akkar directory before external pilot testing.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

يجب بناء دليل عكار والتحقق من الموافقات والاتصالات قبل اختبار خارجي.

### Claim-level sources

- [MOA-EXTENSION-CENTERS] Ministry of Agriculture extension centers list — https://www.agriculture.gov.lb/Subjects/Education-and-Extension/Extension-and-Library/centers-list

## Arabic, English, and local agrifood terminology / المصطلحات الزراعية والغذائية العربية والإنجليزية والمحلية

```yaml
{
  "claim_ids": [
    "claim:kb-terminology:guidance",
    "claim:kb-terminology:decision",
    "claim:kb-terminology:safety"
  ],
  "content_kind": "glossary",
  "dynamicity": "stable",
  "effective_from": null,
  "entities": [],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-scope-local-context",
      "type": "related_to"
    }
  ],
  "id": "kb-terminology",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "crop_disease",
      "polarity": "positive",
      "qualifiers": {
        "context": "local_and_scientific_name"
      },
      "risk": "medium",
      "subject": "diagnosis_workflow",
      "type": "requires_context"
    },
    {
      "evidence_section": "English guidance",
      "object": "crop_disease",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "insect_pest",
      "type": "may_be_confused_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "extension_service",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "professional_referral",
      "type": "requires_context"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "low",
  "source_ids": [],
  "supersedes_legacy_items": [],
  "title_ar": "المصطلحات الزراعية والغذائية العربية والإنجليزية والمحلية",
  "title_en": "Arabic, English, and local agrifood terminology",
  "topics": [
    "practice",
    "terminology",
    "Arabic",
    "Lebanese"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Scientific names should accompany local crop, pest or disease names when identification matters. One local name may refer to multiple organisms, and spelling varies across Arabic and transliteration.

Preferred chatbot wording should be understandable, technically accurate and consistent. Show English in parentheses when it helps equipment labels or source matching. Avoid an overly formal term if users do not recognize it, but do not invent dialect terms.

Glossary record: English; formal Arabic; verified Lebanese/regional term; scientific name; definition; common confusion; preferred wording; spelling variants; transliteration; related terms; source; reviewer; date; geography; production status.

Arabic evaluation must test right-to-left display, mixed units, scientific names, numerals, colloquial queries, Arabizi, spelling errors and whether warnings retain their force.

### Arabic guidance — machine draft

يُذكر الاسم العلمي مع الاسم المحلي للمحصول أو الآفة أو المرض عندما يؤثر التعريف، فقد يدل الاسم المحلي على أكثر من كائن وتختلف الكتابة العربية والنقل بالحروف اللاتينية.

ينبغي أن تكون صياغة المساعد مفهومة ودقيقة ومتسقة. يظهر المصطلح الإنجليزي بين قوسين عندما يساعد على قراءة ملصق أو مطابقة مصدر. لا تستخدم لفظاً رسمياً لا يعرفه المستخدم ولا تخترع لهجة.

حقول المصطلح: الإنجليزية، والعربية الفصحى، واللفظ اللبناني أو الإقليمي الموثّق، والاسم العلمي، والتعريف، والالتباس، والصياغة المفضلة، والتهجئات، والنقل اللاتيني، والمصطلحات المرتبطة، والمصدر، والمراجع، والتاريخ، والجغرافيا، وحالة الإنتاج.

يختبر التقييم العربي اتجاه الكتابة، والوحدات المختلطة، والأسماء العلمية والأرقام، والاستفسار المحكي والعربيزي والأخطاء، وبقاء قوة التحذير.

### Decision logic

If a local term is ambiguous, ask the user to describe it or show context; do not silently map it to one organism or practice.

### منطق القرار — مسودة آلية

إذا كان اللفظ المحلي ملتبساً، اطلب وصفاً أو سياقاً ولا تربطه صامتاً بكائن أو ممارسة واحدة.

### Safe next action

Use an Arabic-speaking agricultural expert and representative users to approve terms in context, not as isolated word substitutions.

### الخطوة التالية الآمنة — مسودة آلية

يعتمد خبير زراعي عربي ومستخدمون ممثلون المصطلح داخل جملة وسياق، لا كترجمة كلمة منفردة.

### Avoid or escalate

Uncertain translations of chemical, veterinary, food-safety or emergency terms remain blocked until reviewed.

### ما يجب تجنبه أو تصعيده — مسودة آلية

تبقى ترجمة مصطلح كيميائي أو بيطري أو غذائي أو طارئ غير مؤكدة محجوبة حتى المراجعة.

### Evidence and applicability limits

Use each term only for its reviewed geography, language community, production system, and technical context.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

تطبق المصطلحات ضمن الجغرافيا ونظام الإنتاج والموسم وحدود الدليل المذكورة.

### Claim-level sources


## Information that requires a dated live source / المعلومات التي تتطلب مصدراً حياً مؤرخاً

```yaml
{
  "claim_ids": [
    "claim:kb-dynamic-information:guidance",
    "claim:kb-dynamic-information:decision",
    "claim:kb-dynamic-information:safety"
  ],
  "content_kind": "policy",
  "dynamicity": "live_only",
  "effective_from": null,
  "entities": [
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "مبيد"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mabid"
        }
      ],
      "id": "pesticide",
      "label_ar": "مبيد زراعي",
      "label_en": "agricultural pesticide",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "veterinary_medicine",
      "label_ar": "دواء بيطري",
      "label_en": "veterinary medicine",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "extreme_weather",
      "label_ar": "طقس متطرف",
      "label_en": "extreme weather",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "alert_window",
      "label_ar": "نافذة التنبيه الحالية",
      "label_en": "current alert window",
      "type": "season"
    },
    {
      "aliases": [],
      "id": "moa_lebanon",
      "label_ar": "وزارة الزراعة اللبنانية",
      "label_en": "Lebanon Ministry of Agriculture",
      "type": "organization"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "LARI"
        },
        {
          "language": "arz",
          "script": "arabic",
          "text": "لاري"
        }
      ],
      "id": "lari",
      "label_ar": "مصلحة الأبحاث العلمية الزراعية",
      "label_en": "Lebanese Agricultural Research Institute",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "market_information_service",
      "label_ar": "خدمة معلومات سوق مؤرخة",
      "label_en": "dated market-information service",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "grant_opportunity",
      "label_ar": "إعلان منحة أو فرصة",
      "label_en": "grant or opportunity call",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "export_condition",
      "label_ar": "شرط تصدير",
      "label_en": "export condition",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "pesticide_register",
      "label_ar": "سجل المبيدات الحالي",
      "label_en": "current pesticide register",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "food_licensing",
      "label_ar": "ترخيص المنشأة الغذائية",
      "label_en": "food-business licensing",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "organic_standard",
      "label_ar": "معيار الإنتاج العضوي",
      "label_en": "organic production standard",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "stale_information",
      "label_ar": "معلومات قديمة",
      "label_en": "stale information",
      "type": "risk"
    }
  ],
  "evidence_class": "official_and_draft_synthesis",
  "expires_at": null,
  "geography": [
    "Akkar",
    "rural Lebanon"
  ],
  "graph_relations": [
    {
      "target": "kb-referrals",
      "type": "requires_live_source"
    }
  ],
  "id": "kb-dynamic-information",
  "languages": [
    "en",
    "ar"
  ],
  "ontology_entities": [
    {
      "aliases": [
        {
          "language": "ar",
          "script": "arabic",
          "text": "مبيد"
        },
        {
          "language": "arz",
          "script": "latin",
          "text": "mabid"
        }
      ],
      "id": "pesticide",
      "label_ar": "مبيد زراعي",
      "label_en": "agricultural pesticide",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "veterinary_medicine",
      "label_ar": "دواء بيطري",
      "label_en": "veterinary medicine",
      "type": "input"
    },
    {
      "aliases": [],
      "id": "extreme_weather",
      "label_ar": "طقس متطرف",
      "label_en": "extreme weather",
      "type": "climate"
    },
    {
      "aliases": [],
      "id": "alert_window",
      "label_ar": "نافذة التنبيه الحالية",
      "label_en": "current alert window",
      "type": "season"
    },
    {
      "aliases": [],
      "id": "moa_lebanon",
      "label_ar": "وزارة الزراعة اللبنانية",
      "label_en": "Lebanon Ministry of Agriculture",
      "type": "organization"
    },
    {
      "aliases": [
        {
          "language": "en",
          "script": "latin",
          "text": "LARI"
        },
        {
          "language": "arz",
          "script": "arabic",
          "text": "لاري"
        }
      ],
      "id": "lari",
      "label_ar": "مصلحة الأبحاث العلمية الزراعية",
      "label_en": "Lebanese Agricultural Research Institute",
      "type": "organization"
    },
    {
      "aliases": [],
      "id": "market_information_service",
      "label_ar": "خدمة معلومات سوق مؤرخة",
      "label_en": "dated market-information service",
      "type": "service"
    },
    {
      "aliases": [],
      "id": "grant_opportunity",
      "label_ar": "إعلان منحة أو فرصة",
      "label_en": "grant or opportunity call",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "export_condition",
      "label_ar": "شرط تصدير",
      "label_en": "export condition",
      "type": "market"
    },
    {
      "aliases": [],
      "id": "pesticide_register",
      "label_ar": "سجل المبيدات الحالي",
      "label_en": "current pesticide register",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "food_licensing",
      "label_ar": "ترخيص المنشأة الغذائية",
      "label_en": "food-business licensing",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "organic_standard",
      "label_ar": "معيار الإنتاج العضوي",
      "label_en": "organic production standard",
      "type": "regulation"
    },
    {
      "aliases": [],
      "id": "stale_information",
      "label_ar": "معلومات قديمة",
      "label_en": "stale information",
      "type": "risk"
    }
  ],
  "ontology_relations": [
    {
      "evidence_section": "English guidance",
      "object": "lari",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "extreme_weather",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "market_information_service",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "grant_opportunity",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "moa_lebanon",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "pesticide_register",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "competent_authority",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "veterinary_medicine",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "competent_authority",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "export_condition",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "competent_authority",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "high",
      "subject": "food_licensing",
      "type": "requires_live_source"
    },
    {
      "evidence_section": "English guidance",
      "object": "alert_window",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "stale_information",
      "type": "conflicts_with"
    },
    {
      "evidence_section": "English guidance",
      "object": "competent_authority",
      "polarity": "positive",
      "qualifiers": {},
      "risk": "medium",
      "subject": "organic_standard",
      "type": "requires_live_source"
    }
  ],
  "ontology_version": "raise-agrifood-ontology-v0.2.0",
  "owner_role": "knowledge_steward",
  "production_eligible": false,
  "publication_scope": "pilot",
  "retrieval_enabled": true,
  "review_by": "2026-11-11",
  "review_status": "ai_draft",
  "reviewer_roles": [
    "domain_expert",
    "Arabic_reviewer",
    "field_reviewer"
  ],
  "risk": "medium",
  "source_ids": [],
  "supersedes_legacy_items": [
    "DYNAMIC-INFORMATION-017"
  ],
  "title_ar": "المعلومات التي تتطلب مصدراً حياً مؤرخاً",
  "title_en": "Information that requires a dated live source",
  "topics": [
    "risk",
    "weather",
    "prices",
    "regulation"
  ],
  "translation_method": "local_repository_ai_draft",
  "translation_status": "machine_draft"
}
```

### English guidance

Weather forecasts, market prices, border or export conditions, grant calls, registered pesticide labels, veterinary alerts, plant-health outbreaks, water interruptions, and regulatory requirements change too quickly for a static guide. The assistant should use an approved tool that displays publisher, timestamp, and geography, or say that it cannot verify the current situation. A previous ministry announcement can explain context but must not be presented as today's price, availability, or rule.

Evidence level describes the support for a claim; answer confidence also depends on retrieval quality and fit to the user's context. A strongly supported international principle may still be locally inapplicable. The system should not transform evidence labels into numerical certainty unless a validated calibration method exists.

Production eligibility is separate: even strong evidence can be blocked because of licensing, privacy, missing local approval, unsafe retrieval context or a superseded version. Approval should occur at claim or subsection level.

### Arabic guidance — machine draft

تتغير توقعات الطقس وأسعار السوق وشروط الحدود أو التصدير ودعوات المنح وبطاقات المبيدات المسجلة والتنبيهات البيطرية وانتشار الآفات والأمراض وانقطاع المياه والمتطلبات التنظيمية بسرعة لا تناسب دليلاً ثابتاً. يجب أن يستخدم المساعد أداة معتمدة تعرض الجهة الناشرة والتاريخ والموقع الجغرافي، أو أن يوضح أنه غير قادر على التحقق من الوضع الحالي. ويمكن لخبر سابق صادر عن الوزارة أن يشرح السياق، لكنه لا يمثل سعر اليوم أو التوفر الحالي أو القاعدة السارية.

تتغير توقعات الطقس وأسعار السوق وشروط الحدود والتصدير والمنح وملصقات المبيدات المسجلة والتنبيهات البيطرية وتفشيات صحة النبات وانقطاع المياه والقواعد التنظيمية أسرع من دليل ثابت. يستخدم المساعد أداة معتمدة تعرض الناشر والوقت والجغرافيا، أو يقول إنه لا يستطيع التحقق. الإعلان القديم يشرح السياق ولا يمثل سعر اليوم أو التوافر أو القاعدة الحالية.

درجة الدليل تصف دعم الادعاء، أما الثقة بالجواب فتتوقف أيضاً على جودة الاسترجاع وملاءمة السياق. قد يكون المبدأ الدولي قوياً وغير ملائم محلياً، ولا تُحوّل درجات الدليل إلى يقين رقمي بلا معايرة موثقة.

أهلية الإنتاج مستقلة عن قوة الدليل؛ قد يُحجب دليل قوي بسبب الترخيص أو الخصوصية أو نقص اعتماد محلي أو سياق استرجاع غير آمن أو نسخة أحدث. يكون الاعتماد على مستوى الادعاء أو القسم.

### Decision logic

If evidence is emerging, conflicting or insufficient, present uncertainty, alternatives and the evidence needed to decide. High-risk content remains blocked until expert and institutional approval.

### منطق القرار — مسودة آلية

إذا كان الدليل ناشئاً أو متعارضاً أو غير كافٍ، اعرض عدم اليقين والبدائل والدليل المطلوب. يبقى المحتوى عالي الخطر محجوباً حتى اعتماد الخبير والمؤسسة.

### Safe next action

Expose a simplified confidence explanation to users and retain the detailed classification for staff, evaluation and audit.

### الخطوة التالية الآمنة — مسودة آلية

اعرض للمستخدم شرحاً مبسطاً للثقة واحتفظ بالتصنيف المفصل للموظفين والتقييم والتدقيق.

### Avoid or escalate

Do not display a high-confidence label solely because retrieval similarity is high.

### ما يجب تجنبه أو تصعيده — مسودة آلية

لا تعرض ثقة عالية لأن تشابه الاسترجاع مرتفع وحده.

### Evidence and applicability limits

Locally expert-approved content should identify reviewer, date, geography and limits; 'local' must not mean all of Lebanon.

### حدود الأدلة وقابلية التطبيق — مسودة آلية

المحتوى المحلي المعتمد يذكر المراجع والتاريخ والجغرافيا والحدود؛ «محلي» لا يعني كل لبنان.

### Claim-level sources


# Non-retrievable source and validation appendix

This appendix is excluded from retrieval. It records provenance, mapping, and unresolved approval work.

### Evidence and source policy

- Prefer current primary official or peer-reviewed passages appropriate to the claim and geography.
- A domain, publisher, or evidence class does not by itself verify a claim; the retained passage must directly support it.
- Separate evidence strength from local applicability, retrieval confidence, review status, and production eligibility.
- Record conflicts, supersession, observation time, expiry, geography, and material limitations instead of silently choosing a source.
- Treat missing passage support as an explicit validation gap; medium/high/critical actions remain limited, refused, or referred as policy requires.
- Dynamic facts remain live evidence and are never promoted into the permanent graph as undated values.

### Source register

```json
[
  {
    "id": "CODEX-FOOD-HYGIENE-CXC1-2022",
    "legacy_ids": [
      "S15"
    ],
    "production_eligible": false,
    "publisher": "Codex Alimentarius Commission (FAO/WHO)",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "Codex Alimentarius Commission (FAO/WHO). General Principles of Food Hygiene (CXC 1-1969). 2022 edition.",
    "url": "https://openknowledge.fao.org/handle/20.500.14283/cc6125en"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Lebanon",
      "regional"
    ],
    "id": "ESDU-ABOUT-2026",
    "legacy_ids": [
      "S02"
    ],
    "production_eligible": false,
    "publisher": "American University of Beirut, Environment and Sustainable Development Unit",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "About ESDU",
    "topics": [
      "ESDU",
      "rural livelihoods",
      "smallholders",
      "women",
      "youth",
      "capacity building"
    ],
    "url": "https://aub.edu.lb/fafs/esdu/Pages/About-ESDU.aspx"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Lebanon"
    ],
    "id": "ESDU-AI-2025",
    "production_eligible": false,
    "publisher": "American University of Beirut",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "ESDU Food Security and AI Initiative",
    "topics": [
      "ESDU",
      "artificial intelligence",
      "food security",
      "entrepreneurship"
    ],
    "url": "https://www.aub.edu.lb/fafs/news/Pages/2025_ExploringSustainabilityandInnovationinLebanonESDULaunchestheFoodSecurityandAIInitiative.aspx"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Akkar",
      "Danniyeh",
      "North Lebanon"
    ],
    "id": "ESDU-AKKAR-VALUECHAINS",
    "legacy_ids": [
      "S04"
    ],
    "production_eligible": false,
    "publisher": "American University of Beirut, ESDU",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "Value Chains for Improved Socioeconomic Well-being of Syrian Refugees and Lebanese Host Communities",
    "topics": [
      "zaatar",
      "coriander",
      "dairy",
      "small ruminants",
      "hydroponic feed",
      "market assessment"
    ],
    "url": "https://www.aub.edu.lb/fafs/esdu/Pages/vcproject.aspx"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Lebanon"
    ],
    "id": "ESDU-ARDI-ARDAK",
    "legacy_ids": [
      "S06"
    ],
    "production_eligible": false,
    "publisher": "American University of Beirut, ESDU",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "Ardi Ardak National Food Security Initiative",
    "topics": [
      "smallholders",
      "rural women",
      "community kitchens",
      "markets",
      "knowledge sharing"
    ],
    "url": "https://www.aub.edu.lb/fafs/esdu/Pages/ardiardakinitiative.aspx"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Akkar",
      "Hasbaya",
      "Baalbek"
    ],
    "id": "ESDU-CLIMAT-AKKAR",
    "legacy_ids": [
      "S05"
    ],
    "production_eligible": false,
    "publisher": "American University of Beirut, ESDU",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "ESDU/WFP climate-resilient livestock and rural livelihoods work in Akkar",
    "topics": [
      "livestock",
      "grazing",
      "sprouting units",
      "composting",
      "rainwater harvesting",
      "renewable energy",
      "living labs"
    ],
    "url": "https://www.aub.edu.lb/fafs/esdu/Documents/ToR_ESDU_Community%20mobilizer_WFP_Akkar%20.pdf"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Lebanon"
    ],
    "id": "ESDU-FARMING-FOR-ALL",
    "production_eligible": false,
    "publisher": "American University of Beirut Continuing Education Center and ESDU",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "Farming For All: Introduction to Sustainable Agriculture",
    "topics": [
      "small-scale farming",
      "soil",
      "water",
      "crops",
      "livestock",
      "post-harvest",
      "waste",
      "marketing"
    ],
    "url": "https://www.aub.edu.lb/cec/Pages/Farming-For-All.aspx"
  },
  {
    "id": "ESDU-HOME-2026",
    "legacy_ids": [
      "S01"
    ],
    "production_eligible": false,
    "publisher": "American University of Beirut (AUB), ESDU",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "American University of Beirut (AUB), ESDU. Environment and Sustainable Development Unit. current page, accessed 2026.",
    "url": "https://www.aub.edu.lb/fafs/esdu/Pages/default.aspx"
  },
  {
    "id": "ESDU-ISNAD",
    "legacy_ids": [
      "S03"
    ],
    "production_eligible": false,
    "publisher": "AUB, ESDU",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "AUB, ESDU. ISNAD: Innovation System Networks for Agricultural Development. project page, accessed 2026.",
    "url": "https://www.aub.edu.lb/fafs/esdu/Pages/ISNADProject.aspx"
  },
  {
    "id": "ESDU-KARIANET",
    "legacy_ids": [
      "S07"
    ],
    "production_eligible": false,
    "publisher": "AUB, ESDU",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "AUB, ESDU. KariaNet. project page, accessed 2026.",
    "url": "https://www.aub.edu.lb/fafs/esdu/Pages/kariaNETmena.aspx"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "North Lebanon",
      "Mount Lebanon"
    ],
    "id": "ESDU-RELEAF",
    "production_eligible": false,
    "publisher": "American University of Beirut, ESDU",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "RE-LEAF legume value-chain project",
    "topics": [
      "legumes",
      "smallholders",
      "agribusiness",
      "employment",
      "markets",
      "capacity building"
    ],
    "url": "https://www.aub.edu.lb/fafs/esdu/Pages/RE-LEAF.aspx"
  },
  {
    "id": "ESDU-RESOLVE",
    "legacy_ids": [
      "S08"
    ],
    "production_eligible": false,
    "publisher": "AUB, ESDU",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "AUB, ESDU. RESOLVE: Resource Empowerment and Sustainability for Optimized Local Value-chain Ecosystems. project page, accessed 2026.",
    "url": "https://www.aub.edu.lb/fafs/esdu/Pages/RESOLVE.aspx"
  },
  {
    "id": "FAO-CLIMATE-LIVESTOCK-2023",
    "legacy_ids": [
      "S20"
    ],
    "production_eligible": false,
    "publisher": "FAO",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "FAO. An analysis of the effects of climate change on livestock. 2023.",
    "url": "https://openknowledge.fao.org/handle/20.500.14283/cc7320en"
  },
  {
    "id": "FAO-CROP-EVAPOTRANSPIRATION-56-2025",
    "legacy_ids": [
      "S11"
    ],
    "production_eligible": false,
    "publisher": "FAO",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "FAO. Crop evapotranspiration: Guidelines for computing crop water requirements, FAO Irrigation and Drainage Paper 56 Rev.1. 2025 revision.",
    "url": "https://openknowledge.fao.org/items/6c5c4d35-ba04-4cb5-8e78-95e9bb59922f"
  },
  {
    "id": "FAO-GREENHOUSE-GAP-2013",
    "legacy_ids": [
      "S23"
    ],
    "production_eligible": false,
    "publisher": "FAO",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "FAO. Good Agricultural Practices for greenhouse vegetable crops. 2013.",
    "url": "https://www.fao.org/3/i3284e/i3284e.pdf"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Lebanon"
    ],
    "id": "FAO-LEBANON-PESTICIDE-CHILD-SAFETY",
    "production_eligible": false,
    "publisher": "Food and Agriculture Organization of the United Nations, Lebanon",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "Protect Children from Pesticides guide released in Arabic",
    "topics": [
      "pesticides",
      "children",
      "workers",
      "occupational safety",
      "Arabic"
    ],
    "url": "https://www.fao.org/lebanon/news/detail/FAO-releases-Protect-Children-from-Pesticides%21-Guide-in-Arabic/en"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Akkar",
      "Lebanon"
    ],
    "id": "FAO-LEBANON-RESILIENT-LIVELIHOODS",
    "legacy_ids": [
      "S10"
    ],
    "production_eligible": false,
    "publisher": "Food and Agriculture Organization of the United Nations",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "Lebanon Plan of Action for Resilient Livelihoods",
    "topics": [
      "rural livelihoods",
      "mixed farming",
      "smallholders",
      "agricultural systems"
    ],
    "url": "https://www.fao.org/fileadmin/user_upload/emergencies/docs/Lebanon%20Plan%20of%20Action%20for%20Resilient%20Livelihoods%202014-2018.pdf"
  },
  {
    "id": "FAO-POSTHARVEST-GRAIN-1996",
    "legacy_ids": [
      "S21"
    ],
    "production_eligible": false,
    "publisher": "FAO",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "FAO. Manual of the Prevention of Post-Harvest Grain Losses. 1996, second edition.",
    "url": "https://www.fao.org/4/x5065e/x5065e00.htm"
  },
  {
    "id": "FAO-SAVE-GROW-2011",
    "legacy_ids": [
      "S24"
    ],
    "production_eligible": false,
    "publisher": "FAO",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "FAO. Save and Grow. 2011.",
    "url": "https://www.fao.org/3/i2215e/i2215e.pdf"
  },
  {
    "id": "FAO-SOIL-TESTING-2019",
    "legacy_ids": [
      "S13"
    ],
    "production_eligible": false,
    "publisher": "FAO",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "FAO. Soil testing methods manual. 2019.",
    "url": "https://openknowledge.fao.org/3/ca2796en/ca2796en.pdf"
  },
  {
    "id": "FAO-WATER-QUALITY-1985",
    "legacy_ids": [
      "S12"
    ],
    "production_eligible": false,
    "publisher": "FAO",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "FAO. Water quality for agriculture. 1985.",
    "url": "https://www.fao.org/4/t0234e/t0234e00.htm"
  },
  {
    "id": "FAO-WHO-PESTICIDE-CODE-2014",
    "legacy_ids": [
      "S14"
    ],
    "production_eligible": false,
    "publisher": "FAO and WHO",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "FAO and WHO. International Code of Conduct on Pesticide Management. 2014, updated guidance available.",
    "url": "https://www.fao.org/pest-and-pesticide-management/pesticide-risk-reduction/code-conduct/en/"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Akkar"
    ],
    "id": "MOA-AKKAR-2026",
    "production_eligible": false,
    "publisher": "Lebanese Ministry of Agriculture",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "time_sensitive": true,
    "title": "Akkar potato season and agricultural production overview, April 2026",
    "topics": [
      "potatoes",
      "pome fruit",
      "olives",
      "citrus",
      "avocado",
      "value chains"
    ],
    "url": "https://www.agriculture.gov.lb/Media/News/2026/%D9%88%D8%B2%D9%8A%D8%B1-%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D8%A9-%D9%86%D8%B2%D8%A7%D8%B1-%D9%87%D8%A7%D9%86%D9%8A-%D9%8A%D8%B7%D9%84%D9%82-%D9%85%D9%86-%D8%B9%D9%83%D8%A7%D8%B1-%D9%85%D9%88%D8%B3%D9%85-%D8%A7%D9%84%D8%A8%D8%B7%D8%A7%D8%B7%D8%A7-2"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Akkar"
    ],
    "id": "MOA-AKKAR-GREENHOUSE-2026",
    "production_eligible": false,
    "publisher": "Lebanese Ministry of Agriculture",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "time_sensitive": true,
    "title": "Ministry monitoring of greenhouse and potato production in Akkar, March 2026",
    "topics": [
      "greenhouses",
      "tomatoes",
      "cucumbers",
      "potatoes",
      "markets"
    ],
    "url": "https://www.agriculture.gov.lb/Media/News/2026/%D9%88%D8%B2%D8%A7%D8%B1%D8%A9-%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D8%A9-%D8%AA%D8%B1%D8%B5%D8%AF-%D8%AA%D8%B7%D9%88%D8%B1-%D8%A7%D9%84%D8%A7%D9%86%D8%AA%D8%A7%D8%AC-%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D9%8A-%D9%81%D9%8A-%D8%B9%D9%83%D8%A7%D8%B1-%D8%B2%D9%8A"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Lebanon"
    ],
    "id": "MOA-BANNED-PESTICIDES-2026",
    "production_eligible": false,
    "publisher": "Lebanese Ministry of Agriculture",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "time_sensitive": true,
    "title": "Current Ministry route for banned agricultural pesticides",
    "topics": [
      "pesticides",
      "banned products",
      "plant protection",
      "regulation"
    ],
    "url": "https://www.agriculture.gov.lb/Subjects/Plant-Resources/Plant-Pharmacy/Banned-Pesticides"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Akkar",
      "Lebanon"
    ],
    "id": "MOA-EXTENSION-CENTERS",
    "production_eligible": false,
    "publisher": "Lebanese Ministry of Agriculture",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "time_sensitive": true,
    "title": "Ministry of Agriculture extension centers list",
    "topics": [
      "extension",
      "referral",
      "farmer support",
      "government services"
    ],
    "url": "https://www.agriculture.gov.lb/Subjects/Education-and-Extension/Extension-and-Library/centers-list"
  },
  {
    "id": "MOA-LEBANON-NAS-2020-2025",
    "legacy_ids": [
      "S09"
    ],
    "production_eligible": false,
    "publisher": "Lebanese Ministry of Agriculture / FAO",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "Lebanese Ministry of Agriculture / FAO. Lebanon National Agriculture Strategy 2020–2025. 2020.",
    "url": "https://faolex.fao.org/docs/pdf/leb202167E.pdf"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Lebanon"
    ],
    "id": "MOA-REGISTERED-PESTICIDES-2026",
    "production_eligible": false,
    "publisher": "Lebanese Ministry of Agriculture",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "time_sensitive": true,
    "title": "Current list of registered agricultural pesticides",
    "topics": [
      "pesticides",
      "registration",
      "plant protection",
      "regulation"
    ],
    "url": "https://www.agriculture.gov.lb/Subjects/Plant-Resources/Plant-Pharmacy/%D8%A7%D9%84%D8%A7%D8%AF%D9%88%D9%8A%D8%A9-%D8%A7%D9%84%D8%B2%D8%B1%D8%A7%D8%B9%D9%8A%D8%A9-%D8%A7%D9%84%D9%85%D8%B3%D9%85%D9%88%D8%AD%D8%A9"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Akkar",
      "Lebanon"
    ],
    "id": "UNDP-IRRIGATION-AKKAR",
    "production_eligible": false,
    "publisher": "UNDP Lebanon",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "Support to host communities through irrigation and water-saving infrastructure",
    "topics": [
      "irrigation",
      "water scarcity",
      "rainwater harvesting",
      "canals",
      "hill lakes"
    ],
    "url": "https://www.undp.org/lebanon/projects/support-host-communities-wash-sector"
  },
  {
    "accessed": "2026-07-29",
    "geography": [
      "Lebanon"
    ],
    "id": "UNDP-LEBANON-NAP-2025",
    "production_eligible": false,
    "publisher": "Lebanese Ministry of Environment and UNDP Lebanon",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "Lebanon National Adaptation Plan 2025–2035",
    "topics": [
      "climate adaptation",
      "agriculture",
      "water",
      "governance",
      "monitoring"
    ],
    "url": "https://www.undp.org/lebanon/publications/lebanon-national-adaptation-plan-nap"
  },
  {
    "id": "WHO-FIVE-KEYS-SAFER-FOOD-2006",
    "legacy_ids": [
      "S16"
    ],
    "production_eligible": false,
    "publisher": "World Health Organization",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "World Health Organization. Five Keys to Safer Food Manual. 2006.",
    "url": "https://www.who.int/publications/i/item/9789241594639"
  },
  {
    "id": "WHO-GROWING-SAFER-PRODUCE-2012",
    "legacy_ids": [
      "S17"
    ],
    "production_eligible": false,
    "publisher": "World Health Organization",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "World Health Organization. Five Keys to Growing Safer Fruits and Vegetables. 2012.",
    "url": "https://www.who.int/publications/i/item/9789241504003"
  },
  {
    "id": "WMO-CLIMATE-SERVICES-2026",
    "legacy_ids": [
      "S22"
    ],
    "production_eligible": false,
    "publisher": "WMO",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "WMO. Weather and climate services. current portal, accessed 2026.",
    "url": "https://wmo.int/"
  },
  {
    "id": "WOAH-ANTIMICROBIAL-USE-2024",
    "legacy_ids": [
      "S19"
    ],
    "production_eligible": false,
    "publisher": "WOAH",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "WOAH. Responsible and prudent use of antimicrobial agents in veterinary medicine, Chapter 6.10. 2024.",
    "url": "https://www.woah.org/fileadmin/Home/eng/Health_standards/tahc/2023/chapitre_antibio_use.pdf"
  },
  {
    "id": "WOAH-CODES-MANUALS-2026",
    "legacy_ids": [
      "S18"
    ],
    "production_eligible": false,
    "publisher": "World Organisation for Animal Health (WOAH)",
    "retrieval_enabled": false,
    "review_status": "official_public_source",
    "source_class": "A",
    "title": "World Organisation for Animal Health (WOAH). Terrestrial Animal Health Code and Manuals. current standards portal, accessed 2026.",
    "url": "https://www.woah.org/en/what-we-do/standards/codes-and-manuals/"
  }
]
```

### Conversion and merge map

```json
{
  "excluded_from_retrieval": {
    "1-2": "product purpose and interface material belongs in product documentation",
    "24": "institution-specific case claims pending passage and institutional review",
    "29-30": "provenance rules and gaps consolidated in this appendix",
    "31": "benchmark material moved to evaluation fixtures",
    "32": "governance and change control belongs in operational documentation",
    "5": "unmeasured product differentiation claim",
    "6": "source authority rules consolidated in this appendix and ingestion validation",
    "9-10": "institutional service and outcome claims pending institutional approval",
    "appendices": "review registers, prompts, dashboards, and readiness checklists are non-retrievable"
  },
  "legacy_json_excluded": {
    "ESDU-IDENTITY-010": "institutional identity belongs in product provenance, not farmer guidance",
    "ESDU-LIVING-LABS-011": "institutional outcome claims require passage and institutional approval",
    "ESDU-LOCAL-FOOD-012": "institutional outcome/service claims require passage and institutional approval",
    "LEGUMES-RELEAF-013": "project-specific outcomes and active opportunities require current official validation"
  },
  "legacy_json_merge_owners": {
    "AKKAR-PROFILE-001": "kb-scope-local-context",
    "AKKAR-SECTOR-002": "kb-scope-local-context",
    "CLIMATE-RISK-014": "kb-climate-season",
    "DYNAMIC-INFORMATION-017": "kb-dynamic-information",
    "EXTENSION-REFERRAL-021": "kb-referrals",
    "FARMER-QUESTION-018": "kb-scope-local-context",
    "GREENHOUSE-DECISIONS-004": "kb-greenhouse",
    "LIVESTOCK-SYSTEMS-008": "kb-livestock",
    "ORCHARD-DECISIONS-005": "kb-crop-production",
    "PESTICIDE-VERIFICATION-019": "kb-ipm-safety",
    "POSTHARVEST-MARKET-015": "kb-postharvest",
    "POTATO-DECISIONS-003": "kb-crop-production",
    "SAFE-ADVICE-016": "kb-ipm-safety",
    "SOIL-FERTILITY-007": "kb-soil-management",
    "VALUE-CHAINS-009": "kb-business-markets",
    "WATER-IRRIGATION-006": "kb-water-irrigation",
    "WORKER-CHILD-SAFETY-020": "kb-ipm-safety"
  },
  "retained_and_merged": {
    "11": [
      "kb-crop-production"
    ],
    "12": [
      "kb-livestock"
    ],
    "13": [
      "kb-soil-management"
    ],
    "14": [
      "kb-water-irrigation"
    ],
    "15": [
      "kb-ipm-safety"
    ],
    "16": [
      "kb-ipm-safety"
    ],
    "17": [
      "kb-climate-season"
    ],
    "18": [
      "kb-greenhouse"
    ],
    "19": [
      "kb-postharvest"
    ],
    "20": [
      "kb-food-processing-safety"
    ],
    "21": [
      "kb-business-markets"
    ],
    "22": [
      "kb-troubleshooting"
    ],
    "23": [
      "kb-decision-rules"
    ],
    "25": [
      "kb-faq"
    ],
    "26": [
      "kb-misconceptions"
    ],
    "27": [
      "kb-referrals"
    ],
    "28": [
      "kb-terminology"
    ],
    "3": [
      "kb-scope-local-context"
    ],
    "4": [
      "kb-scope-local-context"
    ],
    "7": [
      "kb-dynamic-information"
    ],
    "8": [
      "kb-scope-local-context"
    ]
  }
}
```

### Validation backlog

- Obtain expert and field review for every retained draft record and its Arabic wording.
- Verify passage-level entailment, license, archive hash, geography, dates, and supersession for each source.
- Keep current prices, weather, alerts, grants, contacts, pesticide registers, and regulations live-only with observation and expiry times.
- Do not add chemical doses, veterinary treatment, definitive diagnosis, food-processing parameters, or local agronomic thresholds without approved evidence.
- Treat the product restriction on glyphosate recommendations as RAISE policy, not a legal-status claim.
- Confirm institutional services, project outputs, outcomes, contacts, and referral availability before retrieval use.
- Run hidden bilingual retrieval, citation, graph, safety, and farmer/expert preference evaluations before release activation.

Source converted from `ESDU_Agrifood_Knowledge_Base_v0.1.docx`; the source remains unchanged at SHA-256 `3C0BAF8145E4A2E287BA5783F8AB26A7CEAE1C5340322C1EE065887CC9B75B0E`.
