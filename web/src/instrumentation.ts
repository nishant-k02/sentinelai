import { OTLPHttpJsonTraceExporter, registerOTel } from "@vercel/otel";

export function register() {
  registerOTel({
    serviceName: "sentinelai-web",
    traceExporter: new OTLPHttpJsonTraceExporter({
      url:
        process.env.OTEL_EXPORTER_OTLP_ENDPOINT ??
        "http://localhost:4318/v1/traces",
    }),
  });
}
