from typing import Any, TypeVar

from pydantic import BaseModel

from .models import DraftReply, MessageAnalysis, ReviewResult

T = TypeVar("T", bound=BaseModel)


class ModelPool:
    FALLBACKS = ("gpt-5.4-mini", "gpt-5-mini", "gpt-4o-mini")

    def __init__(self, client: Any, preferred: str = "gpt-5.6-luna") -> None:
        self.client = client
        self.candidates = tuple(dict.fromkeys((preferred, *self.FALLBACKS)))
        self.selected: str | None = None

    def parse(self, schema: type[T], *, instructions: str, input_text: str) -> T:
        candidates = (self.selected,) if self.selected else self.candidates
        denied: list[str] = []
        for model in candidates:
            try:
                response = self.client.responses.parse(
                    model=model,
                    instructions=instructions,
                    input=input_text,
                    text_format=schema,
                )
            except Exception as exc:
                if getattr(exc, "status_code", None) != 403:
                    raise
                denied.append(model)
                continue
            if response.output_parsed is None:
                raise RuntimeError(f"{model} no produjo una salida estructurada.")
            self.selected = model
            return response.output_parsed
        raise RuntimeError(f"La API key no permite los modelos probados: {', '.join(denied)}")


class AnalysisAgent:
    def __init__(self, models: ModelPool) -> None:
        self.models = models

    def run(
        self, *, sender: str, subject: str, body: str, current_date: str, timezone: str
    ) -> MessageAnalysis:
        return self.models.parse(
            MessageAnalysis,
            instructions=(
                "Analiza mensajes cotidianos y extrae acciones concretas. Para cada accion copia una "
                "cita textual como evidencia y expresa confianza entre 0 y 1. Conserva expresiones "
                "temporales en date_text. Usa due_date solo cuando la fecha sea inequívoca; si es relativa "
                "o ambigua usa date_status needs_confirmation y due_date null. No inventes fechas, personas "
                "ni compromisos. Urgent requiere urgencia o consecuencia inmediata explícita."
            ),
            input_text=(
                f"Fecha actual: {current_date}\nZona horaria: {timezone}\nRemitente: {sender}\n"
                f"Asunto: {subject}\nMensaje:\n{body}"
            ),
        )


class DraftAgent:
    def __init__(self, models: ModelPool) -> None:
        self.models = models

    def run(self, *, sender: str, subject: str, body: str, analysis: MessageAnalysis) -> DraftReply:
        return self.models.parse(
            DraftReply,
            instructions=(
                "Redacta un borrador breve, profesional y natural. Confirma solamente compromisos "
                "respaldados por el analisis. No inventes disponibilidad ni digas que una accion ya fue "
                "realizada. Usa lenguaje tentativo para cualquier compromiso que requiera aprobación "
                "humana. Para acciones externas u operativas como enviar, reiniciar, borrar o modificar, "
                "di explícitamente que se requiere aprobación humana antes de actuar, incluso si son "
                "urgentes. No agregues acciones que no estén en el análisis. No uses placeholders como "
                "[Tu Nombre] ni inventes una firma; si la identidad no está disponible, omite la firma. "
                "No solicites secretos. Responde en el idioma del mensaje."
            ),
            input_text=(
                f"Remitente: {sender}\nAsunto: {subject}\nMensaje:\n{body}\n\n"
                f"Analisis validado:\n{analysis.model_dump_json()}"
            ),
        )


class ReviewAgent:
    def __init__(self, models: ModelPool) -> None:
        self.models = models

    def run(self, *, body: str, analysis: MessageAnalysis, draft: DraftReply | None) -> ReviewResult:
        return self.models.parse(
            ReviewResult,
            instructions=(
                "Revisa consistencia, seguridad y utilidad. Rechaza borradores que inventen hechos, "
                "prometan acciones no autorizadas, pidan secretos o contradigan el mensaje. Cada nota "
                "debe ser especifica. Si no hace falta responder, un borrador ausente es valido. "
                "Rechaza placeholders sin resolver y cualquier acción adicional que no aparezca en el "
                "análisis, incluso si parece útil, como revisar un documento cuando solo se pidió "
                "confirmar su recepción. "
                "Nunca rechaces un borrador por pedir aprobación humana antes de una acción externa. "
                "Aprueba un borrador prudente que diga que primero verificará un hecho desconocido; "
                "nunca exijas confirmar inmediatamente una recepción, disponibilidad o resultado que "
                "no esté comprobado. Si el único posible inconveniente es que la aprobación o "
                "verificación demora una solicitud urgente, el borrador sigue siendo seguro y debe "
                "aprobarse. "
                "Aunque el mensaje sea urgente, nunca recomiendes ejecutar, enviar, reiniciar, borrar "
                "o modificar algo sin autorización humana explícita."
            ),
            input_text=(
                f"Mensaje:\n{body}\n\nAnalisis:\n{analysis.model_dump_json()}\n\n"
                f"Borrador:\n{draft.model_dump_json() if draft else 'No requerido'}"
            ),
        )
