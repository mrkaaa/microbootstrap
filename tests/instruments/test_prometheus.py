import typing

import litestar
from litestar import status_codes
from litestar.middleware.base import DefineMiddleware
from litestar.testing import AsyncTestClient

from microbootstrap import PrometheusConfig
from microbootstrap.bootstrappers.litestar import LitestarPrometheusInstrument
from microbootstrap.instruments.prometheus_instrument import PrometheusInstrument


def test_prometheus_is_ready(minimal_prometheus_config: PrometheusConfig) -> None:
    prometheus_instrument: typing.Final = PrometheusInstrument(minimal_prometheus_config)
    assert prometheus_instrument.is_ready()


def test_prometheus_bootstrap_is_not_ready(
    minimal_prometheus_config: PrometheusConfig,
) -> None:
    minimal_prometheus_config.prometheus_metrics_path = ""
    prometheus_instrument: typing.Final = PrometheusInstrument(minimal_prometheus_config)
    assert not prometheus_instrument.is_ready()


def test_prometheus_bootstrap_after(
    default_litestar_app: litestar.Litestar,
    minimal_prometheus_config: PrometheusConfig,
) -> None:
    prometheus_instrument: typing.Final = PrometheusInstrument(minimal_prometheus_config)
    assert prometheus_instrument.bootstrap_after(default_litestar_app) == default_litestar_app


def test_prometheus_teardown(
    minimal_prometheus_config: PrometheusConfig,
) -> None:
    prometheus_instrument: typing.Final = PrometheusInstrument(minimal_prometheus_config)
    assert prometheus_instrument.teardown() is None  # type: ignore[func-returns-value]


def test_litestar_prometheus_bootstrap(minimal_prometheus_config: PrometheusConfig) -> None:
    prometheus_instrument: typing.Final = LitestarPrometheusInstrument(minimal_prometheus_config)
    prometheus_instrument.bootstrap()
    prometheus_bootstrap_result: typing.Final = prometheus_instrument.bootstrap_before()

    assert prometheus_bootstrap_result
    assert "route_handlers" in prometheus_bootstrap_result
    assert isinstance(prometheus_bootstrap_result["route_handlers"], list)
    assert len(prometheus_bootstrap_result["route_handlers"]) == 1
    assert "middleware" in prometheus_bootstrap_result
    assert isinstance(prometheus_bootstrap_result["middleware"], list)
    assert len(prometheus_bootstrap_result["middleware"]) == 1
    assert isinstance(prometheus_bootstrap_result["middleware"][0], DefineMiddleware)


async def test_litestar_prometheus_bootstrap_working(minimal_prometheus_config: PrometheusConfig) -> None:
    minimal_prometheus_config.prometheus_metrics_path = "/custom-metrics-path"
    prometheus_instrument: typing.Final = LitestarPrometheusInstrument(minimal_prometheus_config)

    prometheus_instrument.bootstrap()
    litestar_application: typing.Final = litestar.Litestar(
        **prometheus_instrument.bootstrap_before(),
    )

    async with AsyncTestClient(app=litestar_application) as async_client:
        response: typing.Final = await async_client.get(minimal_prometheus_config.prometheus_metrics_path)
        assert response.status_code == status_codes.HTTP_200_OK
        assert response.text
