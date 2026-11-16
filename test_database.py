from app.database import SessionLocal, get_db, make_engine


def test_make_engine_sqlite_em_memoria():
    assert make_engine("sqlite://").dialect.name == "sqlite"


def test_make_engine_sqlite_arquivo():
    assert make_engine("sqlite:///./teste.db").dialect.name == "sqlite"


def test_make_engine_postgres_nao_conecta_ate_ser_usado():
    engine = make_engine("postgresql+psycopg2://u:p@localhost:5432/db")
    assert engine.dialect.name == "postgresql"


def test_get_db_entrega_e_fecha_sessao():
    gen = get_db()
    session = next(gen)
    assert isinstance(session, SessionLocal.class_)
    gen.close()
