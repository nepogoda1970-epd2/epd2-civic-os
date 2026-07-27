const REPOSITORY_VERSION = "0.1.0";
const CANON_VERSION = "0.1.0";

export default function Home() {
  return (
    <main>
      <h1>EPD² Civic OS</h1>
      <p>Infrastructure skeleton</p>
      <dl>
        <dt>Repository version</dt>
        <dd>{REPOSITORY_VERSION}</dd>
        <dt>Canon version</dt>
        <dd>{CANON_VERSION}</dd>
        <dt>Status</dt>
        <dd>ready for the next development package</dd>
      </dl>
    </main>
  );
}
