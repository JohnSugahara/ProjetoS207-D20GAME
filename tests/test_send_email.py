import pytest

from scripts import send_email


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port
        self.sent, self.logged_in, self.tls = [], None, False
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.tls = True

    def login(self, user, password):
        self.logged_in = (user, password)

    def send_message(self, msg):
        self.sent.append(msg)


@pytest.fixture(autouse=True)
def fake_smtp(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(send_email.smtplib, "SMTP", FakeSMTP)


def test_read_coverage(tmp_path):
    path = tmp_path / "coverage.xml"
    path.write_text('<coverage line-rate="0.934"></coverage>')
    assert send_email.read_coverage(str(path)) == "93.4%"


def test_read_coverage_arquivo_ausente_ou_invalido(tmp_path):
    assert send_email.read_coverage(str(tmp_path / "nao-existe.xml")) == "indisponível"
    bad = tmp_path / "bad.xml"
    bad.write_text("isto nao e xml")
    assert send_email.read_coverage(str(bad)) == "indisponível"
    no_attr = tmp_path / "noattr.xml"
    no_attr.write_text("<coverage></coverage>")
    assert send_email.read_coverage(str(no_attr)) == "indisponível"


def test_build_message_usa_destinatario_do_ambiente():
    env = {"NOTIFY_EMAIL": "alguem@exemplo.com"}
    msg = send_email.build_message(env, "SUCCESS", "d20-arena", "7", "http://j/7", "95.0%")
    assert msg["To"] == "alguem@exemplo.com"
    assert msg["Subject"] == "[Jenkins] d20-arena #7 - SUCCESS"
    assert "95.0%" in msg.get_content()


def test_main_sem_notify_email_falha_com_codigo_2(capsys):
    assert send_email.main(["--status", "SUCCESS"], env={}) == 2
    assert "NOTIFY_EMAIL" in capsys.readouterr().err


def test_main_envia_email(tmp_path, capsys):
    env = {
        "NOTIFY_EMAIL": "dev@exemplo.com",
        "SMTP_HOST": "mailpit",
        "SMTP_PORT": "1025",
        "JOB_NAME": "d20-arena",
        "BUILD_NUMBER": "3",
        "BUILD_URL": "http://jenkins/job/3/",
    }
    code = send_email.main(["--status", "FAILURE", "--coverage-file", str(tmp_path / "x.xml")], env=env)
    assert code == 0
    smtp = FakeSMTP.instances[0]
    assert (smtp.host, smtp.port) == ("mailpit", 1025)
    assert smtp.sent[0]["To"] == "dev@exemplo.com"
    assert "FAILURE" in smtp.sent[0]["Subject"]
    assert smtp.logged_in is None and smtp.tls is False
    assert "E-mail enviado" in capsys.readouterr().out


def test_main_com_autenticacao_smtp():
    env = {"NOTIFY_EMAIL": "a@b.com", "SMTP_USER": "u", "SMTP_PASSWORD": "p"}
    assert send_email.main(["--status", "SUCCESS"], env=env) == 0
    smtp = FakeSMTP.instances[0]
    assert smtp.tls is True and smtp.logged_in == ("u", "p")


def test_main_usa_variaveis_do_ambiente_quando_nao_ha_argumentos_opcionais():
    env = {"NOTIFY_EMAIL": "a@b.com"}
    send_email.main(["--status", "UNSTABLE"], env=env)
    assert FakeSMTP.instances[0].sent[0]["Subject"] == "[Jenkins] d20-arena #0 - UNSTABLE"
