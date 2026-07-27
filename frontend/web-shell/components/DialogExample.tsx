"use client";

import { useEffect, useRef, useState } from "react";

export function DialogExample({ onConfirm }: { onConfirm?: () => void }) {
  const [open, setOpen] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const openerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (open && dialog && !dialog.open) {
      dialog.showModal();
      dialog.querySelector<HTMLButtonElement>("[data-dialog-cancel]")?.focus();
    }
  }, [open]);

  function close() {
    dialogRef.current?.close();
    setOpen(false);
    openerRef.current?.focus();
  }

  return (
    <>
      <button
        className="button button--secondary"
        onClick={() => setOpen(true)}
        ref={openerRef}
        type="button"
      >
        Bestätigung öffnen
      </button>
      <dialog aria-labelledby="dialog-title" onCancel={close} ref={dialogRef}>
        <h2 id="dialog-title">Aktion bestätigen</h2>
        <p>
          Diese Fixture führt keine Aktion aus und ist nicht mit einem Backend
          verbunden.
        </p>
        <div className="dialog-actions">
          <button
            className="button button--quiet"
            data-dialog-cancel
            onClick={close}
            type="button"
          >
            Abbrechen
          </button>
          <button
            className="button button--primary"
            onClick={() => {
              onConfirm?.();
              close();
            }}
            type="button"
          >
            Verstanden
          </button>
        </div>
      </dialog>
    </>
  );
}
