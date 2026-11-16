#!/usr/bin/env python3
"""Envia por e-mail o resultado da execução do pipeline Jenkins.

O destinatário NÃO fica no código: vem da variável de ambiente NOTIFY_EMAIL.
Outras variáveis: SMTP_HOST, SMTP_PORT, SMTP_FROM, SMTP_USER, SMTP_PASSWORD.
JOB_NAME, BUILD_NUMBER e BUILD_URL são fornecidas pelo próprio Jenkins.
"""
import argparse
import os
import smtplib
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from email.message import EmailMessage


def read_coverage(path: str = "coverage.xml") -> str:
    """Lê a cobertura total do relatório coverage.xml (atributo line-rate)."""
    try:
        rate = float(ET.parse(path).getroot().attrib["line-rate"])
    except (OSError, ET.ParseError, KeyError, ValueError):
        return "indisponível"
    return f"{rate * 100:.1f}%"


def build_message(env, status, job, build, url, coverage) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"[Jenkins] {job} #{build} - {status}"
    msg["From"] = env.get("SMTP_FROM", "jenkins@d20-arena.local")
    msg["To"] = env["NOTIFY_EMAIL"]
    msg.set_content(
        "\n".join(
            [
                f"Pipeline: {job}",
                f"Build: #{build}",
                f"Status: {status}",
                f"Cobertura de testes: {coverage}",
                f"Detalhes e artefatos: {url}",
                f"Enviado em: {datetime.now():%d/%m/%Y %H:%M:%S}",
            ]
        )
    )
    return msg

# ESSE E PARA O GMAIL
def send(msg: EmailMessage, env) -> None:
    host = env.get("SMTP_HOST", "smtp.gmail.com")
    port = int(env.get("SMTP_PORT", "587"))
    user = env.get("SMTP_USER")
    password = env.get("SMTP_PASSWORD")

    if not user or not password:
        raise RuntimeError("SMTP_USER e SMTP_PASSWORD precisam estar configurados.")

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(user, password)
        smtp.send_message(msg)
# ESSE E PARA O MAILPIT
# def send(msg: EmailMessage, env) -> None:
#     host = env.get("SMTP_HOST", "mailpit")
#     port = int(env.get("SMTP_PORT", "1025"))
#     user = env.get("SMTP_USER")

#     with smtplib.SMTP(host, port, timeout=30) as smtp:
#         if user:
#             # Servidor real (ex.: Gmail): canal cifrado e login.
#             smtp.ehlo()
#             smtp.starttls()
#             smtp.ehlo()
#             smtp.login(user, env.get("SMTP_PASSWORD", ""))
#         # Sem usuário (Mailpit): envio direto, sem TLS nem login.
#         smtp.send_message(msg)


def main(argv=None, env=None) -> int:
    env = os.environ if env is None else env
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", required=True, choices=["SUCCESS", "FAILURE", "UNSTABLE"])
    parser.add_argument("--job", default=env.get("JOB_NAME", "d20-arena"))
    parser.add_argument("--build", default=env.get("BUILD_NUMBER", "0"))
    parser.add_argument("--url", default=env.get("BUILD_URL", "-"))
    parser.add_argument("--coverage-file", default="coverage.xml")
    args = parser.parse_args(argv)

    if not env.get("NOTIFY_EMAIL"):
        print("ERRO: defina a variável de ambiente NOTIFY_EMAIL.", file=sys.stderr)
        return 2

    coverage = read_coverage(args.coverage_file)
    msg = build_message(env, args.status, args.job, args.build, args.url, coverage)
    send(msg, env)
    print(f"E-mail enviado para {env['NOTIFY_EMAIL']} ({args.status}).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
