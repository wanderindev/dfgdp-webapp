import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

/**
 * GenerationDialog is a generic dialog used to inform the user
 * that a generation job is in progress.
 *
 * @param {object} props
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {Function} props.onOpenChange - Callback invoked when the open state changes.
 * @param {string} props.resource - The name of the resource being generated (e.g. "suggestions").
 */
export default function GenerationDialog({ open, onOpenChange, resource }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Generating {resource}</DialogTitle>
        </DialogHeader>
        <p>
          Your {resource.toLowerCase()} are being generated and will be available in a few minutes.
          You can close this dialog and continue working.
        </p>
      </DialogContent>
    </Dialog>
  );
}
