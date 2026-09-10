from __future__ import annotations

import json
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.plans.service import (
    PlanConfigurationError,
    PlanProviderError,
    WEEKDAY_NAMES,
    daily_weekly_plan_service,
)
from app.users.service import UserNotFoundError, user_service
from app.whatsapp.astrology import (
    BirthPlaceNotFoundError,
    BirthTimezoneNotFoundError,
    geocode_birth_place,
)
from app.whatsapp.i18n import normalize_language, t
from app.whatsapp.repository import whatsapp_repository


PLAN_COMMANDS = {"plan", "/plan", "plano", "/plano", "subscription", "assinatura", "suscripción", "suscripcion"}
PLAN_STATES = {
    "PLAN_INFO",
    "PLAN_DAILY_TIME",
    "PLAN_WEEKLY_DAY",
    "PLAN_WEEKLY_TIME",
    "PLAN_BILLING_TYPE",
    "PLAN_CURRENT_LOCATION",
    "PLAN_CHANGE_DAILY_TIME",
    "PLAN_CHANGE_WEEKLY_DAY",
    "PLAN_CHANGE_WEEKLY_TIME",
    "PLAN_CHANGE_LOCATION",
    "PLAN_MENU",
}


def _pick(language: str, en: str, pt: str, es: str) -> str:
    return {"en": en, "pt": pt, "es": es}.get(normalize_language(language), en)


def _with_cancel(language: str, text: str) -> str:
    return t(language, "with_cancel", text=text)


class PlanWhatsAppService:
    def handles(self, *, state: str, text: str) -> bool:
        return state in PLAN_STATES or text.strip().lower() in PLAN_COMMANDS

    def handle_text(
        self,
        *,
        db: Session,
        from_number: str,
        display_name: str | None,
        text: str,
    ) -> list[str | dict] | None:
        clean = text.strip()
        command = clean.lower()
        try:
            user = user_service.get_by_whatsapp(db, from_number)
        except UserNotFoundError:
            return None

        conversation, _ = whatsapp_repository.get_or_create_conversation_by_number(
            db,
            whatsapp_number=from_number,
            user_id=user.id,
        )
        language = normalize_language(conversation.language)

        if command in PLAN_COMMANDS:
            plan = daily_weekly_plan_service.get_for_user(db, user.id)
            if daily_weekly_plan_service.is_active(plan):
                conversation.state = "PLAN_MENU"
                conversation.pending_context = None
                db.commit()
                return [self._active_menu(language, plan)]

            draft = daily_weekly_plan_service.get_or_create_draft(db, user.id)
            # If setup was already completed but payment was not, let the user resume.
            if (
                draft.daily_time is not None
                and draft.weekly_weekday is not None
                and draft.weekly_time is not None
                and draft.billing_type in {"recurring", "one_time"}
                and self._profile_ready(user)
            ):
                location = daily_weekly_plan_service.profile_location(db, user.id)
                if location:
                    try:
                        url = daily_weekly_plan_service.prepare_checkout(
                            db=db, plan=draft, billing_type=draft.billing_type
                        )
                    except ValueError:
                        pass
                    else:
                        conversation.state = "AWAITING_QUESTION"
                        db.commit()
                        return [self._checkout_ready(language, url)]

            conversation.state = "PLAN_INFO"
            conversation.pending_context = None
            db.commit()
            return [self._plan_info(language)]

        state = conversation.state
        if state not in PLAN_STATES:
            return None

        if command in {"cancel", "/cancel", "cancelar", "/cancelar"}:
            conversation.state = "AWAITING_QUESTION"
            conversation.pending_context = None
            db.commit()
            return [t(language, "cancelled"), self.decorate_menu(t(language, "main_menu"), language)]

        plan = daily_weekly_plan_service.get_or_create_draft(db, user.id)

        if state == "PLAN_INFO":
            if command not in {"1", "yes", "sim", "si", "sí", "subscribe", "assinar", "contratar"}:
                if command in {"2", "back", "voltar", "volver"}:
                    conversation.state = "AWAITING_QUESTION"
                    db.commit()
                    return [self.decorate_menu(t(language, "main_menu"), language)]
                return [self._plan_info(language)]
            conversation.state = "PLAN_DAILY_TIME"
            db.commit()
            return [self._daily_time_prompt(language)]

        if state in {"PLAN_DAILY_TIME", "PLAN_CHANGE_DAILY_TIME"}:
            parsed = self._parse_time(clean)
            if parsed is None:
                return [self._daily_time_prompt(language)]
            daily_weekly_plan_service.configure_daily_time(db, plan, parsed)
            if state == "PLAN_CHANGE_DAILY_TIME":
                conversation.state = "PLAN_MENU"
                db.commit()
                return [
                    _pick(language,
                          "✅ Daily Tarot time updated. If today's card was already delivered, the new time will only take effect at least 24 hours after the last delivery.",
                          "✅ Horário do Tarô diário atualizado. Se a carta de hoje já foi enviada, o novo horário só valerá pelo menos 24 horas após o último envio.",
                          "✅ Hora del Tarot diario actualizada. Si la carta de hoy ya fue enviada, el nuevo horario solo se aplicará al menos 24 horas después del último envío."),
                    self._active_menu(language, plan),
                ]
            conversation.state = "PLAN_WEEKLY_DAY"
            db.commit()
            return [self._weekly_day_prompt(language)]

        if state in {"PLAN_WEEKLY_DAY", "PLAN_CHANGE_WEEKLY_DAY"}:
            weekday = self._parse_weekday(clean, language)
            if weekday is None:
                return [self._weekly_day_prompt(language)]
            conversation.pending_context = json.dumps({"weekly_weekday": weekday})
            conversation.state = "PLAN_CHANGE_WEEKLY_TIME" if state == "PLAN_CHANGE_WEEKLY_DAY" else "PLAN_WEEKLY_TIME"
            db.commit()
            return [self._weekly_time_prompt(language, weekday)]

        if state in {"PLAN_WEEKLY_TIME", "PLAN_CHANGE_WEEKLY_TIME"}:
            parsed = self._parse_time(clean)
            if parsed is None:
                weekday = self._pending_weekday(conversation.pending_context)
                return [self._weekly_time_prompt(language, weekday)]
            weekday = self._pending_weekday(conversation.pending_context)
            if weekday is None:
                conversation.state = "PLAN_WEEKLY_DAY"
                db.commit()
                return [self._weekly_day_prompt(language)]
            daily_weekly_plan_service.configure_weekly(db, plan, weekday, parsed)
            conversation.pending_context = None
            if state == "PLAN_CHANGE_WEEKLY_TIME":
                conversation.state = "PLAN_MENU"
                db.commit()
                return [
                    _pick(language,
                          "✅ Weekly astrology schedule updated. If this week's analysis was already delivered, the new schedule will only take effect at least 7 days after the last analysis.",
                          "✅ Agenda da análise astrológica semanal atualizada. Se a análise desta semana já foi enviada, a nova agenda só valerá pelo menos 7 dias após a última análise.",
                          "✅ Agenda del análisis astrológico semanal actualizada. Si el análisis de esta semana ya fue enviado, la nueva agenda solo se aplicará al menos 7 días después del último análisis."),
                    self._active_menu(language, plan),
                ]
            conversation.state = "PLAN_BILLING_TYPE"
            db.commit()
            return [self._billing_prompt(language)]

        if state == "PLAN_BILLING_TYPE":
            billing_type = {
                "1": "recurring", "recurring": "recurring", "mensal": "recurring", "monthly": "recurring",
                "2": "one_time", "one-time": "one_time", "one time": "one_time", "avulso": "one_time", "único": "one_time", "unico": "one_time",
            }.get(command)
            if billing_type is None:
                return [self._billing_prompt(language)]
            plan.billing_type = billing_type
            db.commit()

            if not self._profile_ready(user):
                conversation.state = "AWAITING_QUESTION"
                db.commit()
                return [
                    _pick(language,
                          "⚠️ Your schedule was saved, but before payment you must complete PROFILE with date of birth, exact birth time and birthplace so the weekly analysis can use your full natal chart. After completing it, send PLAN again to continue.",
                          "⚠️ Sua agenda foi salva, mas antes do pagamento você precisa completar o PERFIL com data de nascimento, hora exata de nascimento e local de nascimento para que a análise semanal use seu mapa astral completo. Depois de completar, envie PLANO novamente para continuar.",
                          "⚠️ Tu agenda fue guardada, pero antes del pago debes completar PERFIL con fecha de nacimiento, hora exacta y lugar de nacimiento para que el análisis semanal use tu carta natal completa. Después, envía PLAN nuevamente para continuar."),
                    self.decorate_menu(t(language, "main_menu"), language),
                ]

            location = daily_weekly_plan_service.profile_location(db, user.id)
            if location is None:
                conversation.state = "PLAN_CURRENT_LOCATION"
                conversation.pending_context = json.dumps({"billing_type": billing_type})
                db.commit()
                return [self._current_location_prompt(language)]

            url = daily_weekly_plan_service.prepare_checkout(db=db, plan=plan, billing_type=billing_type)
            conversation.state = "AWAITING_QUESTION"
            conversation.pending_context = None
            db.commit()
            return [self._checkout_ready(language, url)]

        if state in {"PLAN_CURRENT_LOCATION", "PLAN_CHANGE_LOCATION"}:
            try:
                place = geocode_birth_place(clean, language=language)
            except (BirthPlaceNotFoundError, BirthTimezoneNotFoundError, httpx.HTTPError, ValueError):
                return [self._current_location_prompt(language)]
            daily_weekly_plan_service.save_current_location(
                db=db,
                user_id=user.id,
                place=place.display_name,
                latitude=place.latitude,
                longitude=place.longitude,
                timezone_name=place.timezone,
            )
            if state == "PLAN_CHANGE_LOCATION":
                conversation.state = "PLAN_MENU"
                db.commit()
                return [
                    _pick(language,
                          f"📍 Current location updated to {place.display_name}. Weekly astrology and future delivery times will use timezone {place.timezone}.",
                          f"📍 Local atual atualizado para {place.display_name}. A astrologia semanal e os próximos horários usarão o fuso {place.timezone}.",
                          f"📍 Ubicación actual actualizada a {place.display_name}. La astrología semanal y los próximos horarios usarán la zona {place.timezone}."),
                    self._active_menu(language, plan),
                ]

            billing_type = plan.billing_type or self._pending_billing(conversation.pending_context)
            if billing_type not in {"recurring", "one_time"}:
                conversation.state = "PLAN_BILLING_TYPE"
                db.commit()
                return [self._billing_prompt(language)]
            url = daily_weekly_plan_service.prepare_checkout(db=db, plan=plan, billing_type=billing_type)
            conversation.state = "AWAITING_QUESTION"
            conversation.pending_context = None
            db.commit()
            return [
                _pick(language,
                      f"📍 Current location saved as {place.display_name}. Keep this updated whenever you travel or move so the weekly forecast and local timing remain as accurate as possible.",
                      f"📍 Local atual salvo como {place.display_name}. Atualize sempre que viajar ou mudar de cidade para manter a análise semanal e os horários locais o mais precisos possível.",
                      f"📍 Ubicación actual guardada como {place.display_name}. Actualízala cuando viajes o cambies de ciudad para mantener el análisis semanal y los horarios locales lo más precisos posible."),
                self._checkout_ready(language, url),
            ]

        if state == "PLAN_MENU":
            if command == "1":
                conversation.state = "PLAN_CHANGE_DAILY_TIME"
                db.commit()
                return [self._daily_time_prompt(language)]
            if command == "2":
                conversation.state = "PLAN_CHANGE_WEEKLY_DAY"
                db.commit()
                return [self._weekly_day_prompt(language)]
            if command == "3":
                conversation.state = "PLAN_CHANGE_LOCATION"
                db.commit()
                return [self._current_location_prompt(language)]
            if command == "4":
                try:
                    daily_weekly_plan_service.cancel_renewal(db=db, plan=plan)
                except (ValueError, PlanConfigurationError, PlanProviderError):
                    return [_pick(language,
                        "I couldn't cancel renewal right now. Please try again shortly.",
                        "Não consegui cancelar a renovação agora. Tente novamente em instantes.",
                        "No pude cancelar la renovación ahora. Inténtalo de nuevo en unos instantes.")]
                conversation.state = "AWAITING_QUESTION"
                db.commit()
                end = plan.current_period_end.date().isoformat() if plan.current_period_end else "the end of the paid period"
                return [
                    _pick(language,
                          f"✅ Automatic renewal is cancelled. Your plan remains active until {end}; there will be no new automatic charge after that.",
                          f"✅ A renovação automática foi cancelada. Seu plano continua ativo até {end}; depois disso não haverá nova cobrança automática.",
                          f"✅ La renovación automática fue cancelada. Tu plan seguirá activo hasta {end}; después no habrá un nuevo cobro automático."),
                    self.decorate_menu(t(language, "main_menu"), language),
                ]
            return [self._active_menu(language, plan)]

        return None

    @staticmethod
    def decorate_menu(message: str, language: str) -> str:
        addition = _pick(
            language,
            "\nPLAN — Daily Tarot + weekly astrology plan",
            "\nPLANO — Tarô diário + astrologia semanal",
            "\nPLAN — Tarot diario + astrología semanal",
        )
        return message if "PLANO —" in message or "PLAN —" in message else message + addition

    @staticmethod
    def decorate_profile_menu(message: str, language: str) -> str:
        addition = _pick(
            language,
            "\n5 — Current location (update whenever you travel/move)",
            "\n5 — Local atual (atualize sempre que viajar/mudar)",
            "\n5 — Ubicación actual (actualízala cuando viajes/te mudes)",
        )
        return message if "5 —" in message else message + addition

    @staticmethod
    def _profile_ready(user) -> bool:
        p = user.profile
        return bool(p and p.birth_date and p.birth_time and p.birth_place and p.natal_chart)

    @staticmethod
    def _parse_time(value: str):
        try:
            return datetime.strptime(value.strip(), "%H:%M").time()
        except ValueError:
            return None

    @staticmethod
    def _parse_weekday(value: str, language: str) -> int | None:
        normalized = value.strip().lower()
        mapping = {
            "1": 0, "monday": 0, "segunda": 0, "segunda-feira": 0, "lunes": 0,
            "2": 1, "tuesday": 1, "terça": 1, "terca": 1, "martes": 1,
            "3": 2, "wednesday": 2, "quarta": 2, "miércoles": 2, "miercoles": 2,
            "4": 3, "thursday": 3, "quinta": 3, "jueves": 3,
            "5": 4, "friday": 4, "sexta": 4, "viernes": 4,
            "6": 5, "saturday": 5, "sábado": 5, "sabado": 5,
            "7": 6, "sunday": 6, "domingo": 6,
        }
        return mapping.get(normalized)

    @staticmethod
    def _pending_weekday(value: str | None) -> int | None:
        try:
            result = int(json.loads(value or "{}").get("weekly_weekday"))
            return result if 0 <= result <= 6 else None
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    @staticmethod
    def _pending_billing(value: str | None) -> str | None:
        try:
            result = json.loads(value or "{}").get("billing_type")
            return str(result) if result else None
        except (TypeError, json.JSONDecodeError):
            return None

    @staticmethod
    def _plan_info(language: str) -> str:
        return _with_cancel(language, _pick(
            language,
            "🌙 *Daily Tarot + Weekly Astrology*\n\nWith this plan you choose a time to receive one Tarot card every day, with a focused interpretation for that day: advice, cautions, opportunities and practical suggestions. You also choose one weekday and time to receive a full astrological outlook for the next seven days, crossing your natal chart with current transits and your current location.\n\nFor weekly astrology you must complete PROFILE with date of birth, exact birth time and birthplace. You must also keep your *current location* updated whenever you travel or move; location and timezone affect the weekly calculation and delivery times.\n\nRecurring: US$10/month or R$60/month.\nOne-month, no renewal: US$11 or R$66.\n\n1 — Configure and subscribe\n2 — Back",
            "🌙 *Tarô Diário + Astrologia Semanal*\n\nCom este plano você escolhe um horário para receber uma carta de Tarô todos os dias, com uma interpretação focada naquele dia: conselhos, avisos, oportunidades e sugestões práticas. Você também escolhe um dia da semana e horário para receber uma análise astrológica ampla dos próximos sete dias, cruzando seu mapa natal com os trânsitos atuais e seu local atual.\n\nPara a astrologia semanal, é necessário completar o PERFIL com data de nascimento, hora exata e local de nascimento. Você também deve manter o *local atual* sempre atualizado quando viajar ou mudar de cidade; local e fuso influenciam o cálculo semanal e os horários de envio.\n\nRecorrente: US$10/mês ou R$60/mês.\nAvulso por um mês, sem renovação: US$11 ou R$66.\n\n1 — Configurar e contratar\n2 — Voltar",
            "🌙 *Tarot Diario + Astrología Semanal*\n\nCon este plan eliges una hora para recibir una carta de Tarot cada día, con interpretación enfocada en ese día: consejos, advertencias, oportunidades y sugerencias prácticas. También eliges un día y hora semanal para recibir un análisis astrológico amplio de los próximos siete días, cruzando tu carta natal con los tránsitos actuales y tu ubicación actual.\n\nPara la astrología semanal debes completar PERFIL con fecha de nacimiento, hora exacta y lugar de nacimiento. Mantén también tu *ubicación actual* actualizada cuando viajes o te mudes; la ubicación y zona horaria afectan el cálculo semanal y los horarios de envío.\n\nRecurrente: US$10/mes o R$60/mes.\nUn mes sin renovación: US$11 o R$66.\n\n1 — Configurar y contratar\n2 — Volver",
        ))

    @staticmethod
    def _daily_time_prompt(language: str) -> str:
        return _with_cancel(language, _pick(language,
            "What time would you like to receive your daily Tarot card? Send HH:MM, for example 08:30.",
            "Que horas você quer receber sua carta diária de Tarô? Envie HH:MM, por exemplo 08:30.",
            "¿A qué hora quieres recibir tu carta diaria de Tarot? Envía HH:MM, por ejemplo 08:30."))

    @staticmethod
    def _weekly_day_prompt(language: str) -> str:
        return _with_cancel(language, _pick(language,
            "Choose the weekday for your weekly astrology analysis:\n1 Monday\n2 Tuesday\n3 Wednesday\n4 Thursday\n5 Friday\n6 Saturday\n7 Sunday",
            "Escolha o dia da análise astrológica semanal:\n1 Segunda\n2 Terça\n3 Quarta\n4 Quinta\n5 Sexta\n6 Sábado\n7 Domingo",
            "Elige el día del análisis astrológico semanal:\n1 Lunes\n2 Martes\n3 Miércoles\n4 Jueves\n5 Viernes\n6 Sábado\n7 Domingo"))

    @staticmethod
    def _weekly_time_prompt(language: str, weekday: int | None) -> str:
        day = WEEKDAY_NAMES[weekday] if weekday is not None and 0 <= weekday <= 6 else "selected day"
        return _with_cancel(language, _pick(language,
            f"What time on {day} should I send the weekly analysis? Send HH:MM, for example 19:00.",
            "Em qual horário desse dia devo enviar a análise semanal? Envie HH:MM, por exemplo 19:00.",
            "¿A qué hora de ese día debo enviar el análisis semanal? Envía HH:MM, por ejemplo 19:00."))

    @staticmethod
    def _billing_prompt(language: str) -> str:
        return _with_cancel(language, _pick(language,
            "Choose payment type:\n1 — Automatic monthly renewal: US$10 / R$60 per month\n2 — One month only, no renewal: US$11 / R$66",
            "Escolha o tipo de pagamento:\n1 — Renovação mensal automática: US$10 / R$60 por mês\n2 — Um mês avulso, sem renovação: US$11 / R$66",
            "Elige el tipo de pago:\n1 — Renovación mensual automática: US$10 / R$60 al mes\n2 — Un mes solamente, sin renovación: US$11 / R$66"))

    @staticmethod
    def _current_location_prompt(language: str) -> str:
        return _with_cancel(language, _pick(language,
            "📍 Send your current city, state/region and country. This is different from your birthplace and should be updated whenever you travel or move.",
            "📍 Envie sua cidade atual, estado/região e país. Isso é diferente do seu local de nascimento e deve ser atualizado sempre que você viajar ou mudar de cidade.",
            "📍 Envía tu ciudad actual, estado/región y país. Esto es diferente de tu lugar de nacimiento y debes actualizarlo cuando viajes o te mudes."))

    @staticmethod
    def _checkout_ready(language: str, url: str) -> str:
        return _pick(language,
            f"✅ Your schedule is ready. Open the link below, choose USD or BRL and complete payment:\n{url}",
            f"✅ Sua agenda está pronta. Abra o link abaixo, escolha dólar ou real e conclua o pagamento:\n{url}",
            f"✅ Tu agenda está lista. Abre el enlace, elige USD o BRL y completa el pago:\n{url}")

    @staticmethod
    def _active_menu(language: str, plan) -> str:
        weekday = WEEKDAY_NAMES[plan.weekly_weekday] if plan.weekly_weekday is not None else "?"
        daily = plan.daily_time.strftime("%H:%M") if plan.daily_time else "?"
        weekly = plan.weekly_time.strftime("%H:%M") if plan.weekly_time else "?"
        renewal = "off" if plan.cancel_at_period_end or plan.billing_type == "one_time" else "on"
        return _with_cancel(language, _pick(language,
            f"🌙 *Your plan*\nDaily Tarot: {daily}\nWeekly astrology: {weekday} at {weekly}\nAutomatic renewal: {renewal}\n\n1 — Change daily time\n2 — Change weekly day/time\n3 — Update current location\n4 — Cancel renewal",
            f"🌙 *Seu plano*\nTarô diário: {daily}\nAstrologia semanal: {weekday} às {weekly}\nRenovação automática: {renewal}\n\n1 — Alterar horário diário\n2 — Alterar dia/horário semanal\n3 — Atualizar local atual\n4 — Cancelar renovação",
            f"🌙 *Tu plan*\nTarot diario: {daily}\nAstrología semanal: {weekday} a las {weekly}\nRenovación automática: {renewal}\n\n1 — Cambiar hora diaria\n2 — Cambiar día/hora semanal\n3 — Actualizar ubicación actual\n4 — Cancelar renovación"))


plan_whatsapp_service = PlanWhatsAppService()
