"""
ORCHESTRATOR - The Central Nervous System of the Zophiel Mind  v3
30-module pipeline with RAG-grounded humanlike synthesis.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any

from brain.mind.listener         import listen, InputSignal
from brain.mind.understander     import understand, Comprehension
from brain.mind.pattern_detector import scan, PatternReport
from brain.mind.ponderer         import ponder, PonderResult
from brain.mind.questioner       import generate_questions, QuestionSet
from brain.mind.logic_engine     import analyse, LogicResult
from brain.mind.archetype        import profile_text, ArchetypeProfile
from brain.mind.cross_domain     import reason, CrossDomainResult
from brain.mind.learner          import absorb, recall
from brain.mind.self_reflector   import audit, ReflectionAudit
from brain.mind.occult_framework import apply as occult_apply, read as occult_read, OccultSignature
from brain.mind.speaker          import speak

from brain.mind.working_memory         import push as wm_push, get_state as wm_state, resolve_pronouns
from brain.mind.salience_filter        import filter_salience, SalienceResult
from brain.mind.contradiction_handler  import check_contradictions, ContradictionReport
from brain.mind.analogy_engine         import generate_analogy, AnalogyResult
from brain.mind.confidence_calibration import calibrate, hedge_phrase, CalibrationResult
from brain.mind.theory_of_mind         import model_intent, IntentModel
from brain.mind.intuition_fast_path    import fast_answer, FastAnswer
from brain.mind.temporal_reasoning     import analyse_time, TemporalContext
from brain.mind.spell_normalizer       import normalize_query
from brain.mind.query_expander         import expand_query
from brain.mind.humanlike_synthesizer  import synthesize, SynthesisResult

from brain.mind.asher_logic_engine       import get_asher_engine, AsherAnalysis
from brain.mind.emotional_inertia_engine import get_emotional_engine, EmotionalContext
from brain.mind.circadian_state_engine   import get_context as circadian_context, CircadianContext
from brain.mind.ego_defense_engine       import get_defense_engine, DefenseResponse
from brain.mind.social_hierarchy_engine  import get_hierarchy_engine, HierarchyContext
from brain.mind.psycholinguistic_decoder import decode as psy_decode, generate_response_directives
from brain.mind.pisp_framework           import get_pisp, PISPResult
from brain.mind.zophiel_knowledge_base   import get_kb

from brain.vector_rag import get_rag_index


@dataclass
class MindResponse:
    query: str
    answer: str
    intent: str
    confidence: float
    confidence_label: str
    threat_level: str
    hypotheses: list[str]
    cross_domain_insight: str
    archetype: str
    clarification_needed: bool
    clarifying_question: str
    audit_score: float
    occult_phase: str
    processing_ms: float
    fast_path_used: bool
    analogy: str
    temporal_note: str
    hidden_need: str
    raw: dict[str, Any] = field(default_factory=dict)


class ZophielMind:

    def think(self, raw_input: str | dict | bytes, context: dict | None = None) -> MindResponse:
        t0 = time.time()
        ctx = context or {}
        text_raw = raw_input if isinstance(raw_input, str) else str(raw_input)

        normalized, was_corrected = normalize_query(text_raw)

        fast: FastAnswer | None = fast_answer(normalized)
        if fast and fast.confidence >= 0.95:
            wm_push('user', normalized)
            wm_push('assistant', fast.answer)
            elapsed = (time.time() - t0) * 1000
            return MindResponse(
                query=text_raw, answer=fast.answer,
                intent='calculation', confidence=fast.confidence,
                confidence_label='high confidence',
                threat_level='none', hypotheses=[],
                cross_domain_insight='', archetype='',
                clarification_needed=False, clarifying_question='',
                audit_score=1.0, occult_phase='', processing_ms=round(elapsed, 2),
                fast_path_used=True, analogy='', temporal_note='', hidden_need='',
            )

        psy_profile = psy_decode(normalized)
        psy_directives = generate_response_directives(psy_profile)

        hierarchy_ctx: HierarchyContext = get_hierarchy_engine().process_turn(normalized)
        emotional_ctx: EmotionalContext = get_emotional_engine().process_turn(normalized)
        circ_ctx: CircadianContext = circadian_context()
        pisp_result: PISPResult = get_pisp().run(normalized)

        wm_push('user', normalized)
        resolved = resolve_pronouns(normalized)

        salience: SalienceResult = filter_salience(resolved)
        query = salience.core_query if not salience.is_trivial else resolved

        intent_model: IntentModel = model_intent(resolved)
        temporal: TemporalContext = analyse_time(resolved)

        signal: InputSignal = listen(query)
        comp: Comprehension = understand(signal)
        patterns: PatternReport = scan(signal.text)
        questions: QuestionSet = generate_questions(comp, ctx)

        primary_domain = comp.domain_hints[0] if comp.domain_hints else 'science'

        asher_analysis: AsherAnalysis = get_asher_engine().process(query)

        kb_hits = get_kb().query(query, top_k=2)
        kb_context_str = get_kb().format_hits(kb_hits) if kb_hits else ''

        top_rag_score = 0.0
        hit_texts: list[str] = []
        try:
            idx = get_rag_index()
            expanded_q = expand_query(query, detected_domain=primary_domain)
            hits = idx.query(expanded_q, top_k=10)
            if hits:
                top_rag_score = hits[0].score
                hit_texts = [h.text for h in hits]
        except Exception as _rag_err:
            import logging
            logging.getLogger(__name__).warning("RAG error: %s", _rag_err)

        # When domain is in KB-primary zones, verify RAG hits are actually on-topic.
        # If the top RAG result doesn't contain domain keywords, replace with KB content.
        _WEAK_RAG_DOMAINS = {"THEOLOGY", "ASTROLOGY", "HISTORY"}
        from brain.vector_rag import _detect_source_filter as _dsf, _DOMAIN_KEYWORDS
        _detected_domain = _dsf(query)
        if kb_hits and _detected_domain in _WEAK_RAG_DOMAINS:
            _domain_kws = _DOMAIN_KEYWORDS.get(_detected_domain, set())
            _top_text_lc = hit_texts[0].lower() if hit_texts else ""
            _rag_on_topic = sum(1 for kw in _domain_kws if kw in _top_text_lc) >= 2
            if not _rag_on_topic:
                # RAG result is off-domain — use KB exclusively
                hit_texts = [f"{e.topic}: {e.content}" for e in kb_hits]
                top_rag_score = 0.72  # signal-grade for internal KB

        topic_str = comp.topics[0] if comp.topics else query[:60]
        defense_resp: DefenseResponse = get_defense_engine().process_turn(
            normalized, topic=topic_str
        )

        analogy: AnalogyResult = generate_analogy(topic_str, context=query)
        cross: CrossDomainResult = reason(query, primary_domain)

        synth: SynthesisResult = synthesize(
            question=query,
            hit_texts=hit_texts,
            analogy=analogy.best_analogy,
            cross_domain=cross.synthesis,
            confidence=top_rag_score,
            emotional_context=emotional_ctx,
            circadian_context=circ_ctx,
            hierarchy_context=hierarchy_ctx,
            defense_response=defense_resp,
            asher_analysis=asher_analysis,
            kb_context=kb_context_str,
            pisp_plan=pisp_result.plan,
        )

        absorb(query, source='user_input', domain=primary_domain)
        recalled = recall(query, domain=primary_domain)

        if synth.has_real_content:
            draft = synth.answer
            if recalled:
                facts_str = '; '.join(e.fact for e in recalled[:1])
                draft += f" (From our earlier conversation: {facts_str}.)"
        else:
            ponder_result: PonderResult = ponder(comp, ctx)
            logic: LogicResult = analyse(ponder_result.best_hypothesis.statement)
            draft = ponder_result.best_hypothesis.statement
            if cross.synthesis:
                draft += f" {cross.synthesis}"
            if analogy.best_analogy and 'systematic principles' not in analogy.best_analogy:
                draft += f" To picture it: {analogy.best_analogy}."

        contradiction: ContradictionReport = check_contradictions(draft)
        if contradiction.has_conflict:
            draft = contradiction.resolved_text

        calib: CalibrationResult = calibrate(
            rag_score=top_rag_score,
            logic_strength=0.6 if synth.has_real_content else 0.3,
            contradiction_penalty=contradiction.confidence_penalty,
            query_clarity=salience.salience_score,
            has_web_source=ctx.get('has_web_source', False),
            domain_match=bool(comp.domain_hints),
        )
        if calib.should_hedge:
            draft = hedge_phrase(calib.label) + draft

        reflection: ReflectionAudit = audit(draft, query)
        if not reflection.passed and reflection.revised != draft:
            draft = reflection.revised

        occ: OccultSignature = occult_read(topic_str)
        draft = occult_apply(draft, query)

        tone = self._pick_tone(comp, intent_model)
        final_answer = speak(draft, tone=tone)

        if temporal.temporal_note:
            final_answer += f' {temporal.temporal_note}'

        wm_push('assistant', final_answer)
        elapsed_ms = (time.time() - t0) * 1000

        try:
            arch: ArchetypeProfile = profile_text(query)
            arch_str = f"{arch.primary_archetype} (shadow: {arch.shadow_archetype})"
        except Exception:
            arch_str = ''

        return MindResponse(
            query=text_raw,
            answer=final_answer,
            intent=intent_model.inferred_intent,
            confidence=calib.score,
            confidence_label=calib.label,
            threat_level=patterns.threat_level,
            hypotheses=[],
            cross_domain_insight=cross.synthesis,
            archetype=arch_str,
            clarification_needed=questions.should_ask,
            clarifying_question=questions.primary if questions.should_ask else '',
            audit_score=reflection.audit_score,
            occult_phase=occ.current_cycle_phase,
            processing_ms=round(elapsed_ms, 2),
            fast_path_used=False,
            analogy=analogy.best_analogy,
            temporal_note=temporal.temporal_note,
            hidden_need=intent_model.hidden_need,
            raw={
                'normalized_input': normalized,
                'was_spell_corrected': was_corrected,
                'rag_score': top_rag_score,
                'facts_used': synth.facts_used,
                'confidence': {'score': calib.score, 'label': calib.label},
                'intent_model': {
                    'inferred': intent_model.inferred_intent,
                    'hidden_need': intent_model.hidden_need,
                },
                'temporal': {'sensitive': temporal.is_time_sensitive, 'era': temporal.era},
                'contradiction': {'has_conflict': contradiction.has_conflict},
                'domains': comp.domain_hints,
                'keywords': comp.keywords[:5],
                'emotion': {
                    'state': emotional_ctx.current_emotion,
                    'intensity': emotional_ctx.intensity,
                },
                'circadian': {
                    'phase': circ_ctx.phase_name,
                    'hour': circ_ctx.current_hour,
                },
                'hierarchy': {
                    'register': hierarchy_ctx.register,
                    'delta': hierarchy_ctx.status_delta,
                },
                'defense': {
                    'type': defense_resp.defense_type,
                    'active': defense_resp.is_active,
                },
                'pisp': {
                    'query_class': pisp_result.deconstruction.query_class,
                    'real_question': pisp_result.deconstruction.real_question,
                },
                'asher_chains': len(asher_analysis.equation_chains),
                'kb_hits': len(kb_hits),
                'psy_flags': {
                    'deception_score': psy_profile.deception_score,
                    'attachment_style': psy_profile.attachment_style,
                },
            },
        )

    def _pick_tone(self, comp: Comprehension, intent_model: IntentModel) -> str:
        if intent_model.emotional_subtext == 'frustration':
            return 'empathetic'
        if intent_model.inferred_intent in ('learn', 'explore'):
            return 'explanatory'
        if intent_model.inferred_intent == 'decide':
            return 'direct'
        if comp.intent == 'question':
            return 'explanatory'
        return 'direct'


_mind = ZophielMind()


def think(raw_input: str | dict | bytes, context: dict | None = None) -> MindResponse:
    return _mind.think(raw_input, context)


def ask(question: str) -> str:
    return _mind.think(question).answer
