import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = {
  children: ReactNode;
  /** `screen`: fallback for the whole app. `section`: notice inside the step that failed. */
  variant?: "screen" | "section";
  /** When this value changes (for example, the person moves to another step), the boundary resets. */
  resetKey?: unknown;
};

type State = { error: Error | null };

/**
 * Catches rendering errors so one broken part does not blank the whole page.
 * API errors are not caught here: the API client turns them into messages inside each section.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unexpected render error", error, info.componentStack);
  }

  componentDidUpdate(previous: Props) {
    if (this.state.error && previous.resetKey !== this.props.resetKey) this.setState({ error: null });
  }

  private retry = () => this.setState({ error: null });

  render() {
    if (!this.state.error) return this.props.children;
    if (this.props.variant === "screen") {
      return (
        <main className="fallback-screen" role="alert">
          <img className="fallback-screen__logo" src="/conco-logo.png" alt="Conco" />
          <h1>Algo salió mal</h1>
          <p>Ocurrió un error inesperado al mostrar la página. Probá de nuevo; si sigue pasando, volvé más tarde.</p>
          <button className="primary" type="button" onClick={this.retry}>Reintentar</button>
        </main>
      );
    }
    return (
      <div className="notice notice--error" role="alert">
        <span className="notice-icon">!</span>
        <div>
          <strong>No pudimos mostrar esta sección</strong>
          <p>Ocurrió un error inesperado. Probá de nuevo.</p>
          <button className="secondary notice-action" type="button" onClick={this.retry}>Reintentar</button>
        </div>
      </div>
    );
  }
}
