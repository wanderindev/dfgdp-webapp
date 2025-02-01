import React from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

/**
 * A generic confirmation dialog.
 *
 * @param {object} props
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {string} props.title - The title of the dialog.
 * @param {string} props.description - The description of the dialog.
 * @param {Function} props.onConfirm - Callback executed when the "Continue" action is clicked.
 * @param {Function} props.onClose - Callback executed when the dialog should be closed.
 */
export default function ConfirmationDialog({
  open,
  title,
  description,
  onConfirm,
  onClose,
}) {
  return (
    <AlertDialog
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) {
          onClose();
        }
      }}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => {
              // Execute the confirmation action and then close the dialog.
              onConfirm();
              onClose();
            }}
          >
            Continue
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
