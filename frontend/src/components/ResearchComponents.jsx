import React from 'react';
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import RichTextEditor from '@/components/ui/RichTextEditor';

// Research review dialog
export const ResearchReviewDialog = ({
  research,
  hasArticle,
  isOpen,
  onClose,
  onSave,
  onApprove,
  onReject,
  onMakePending,
}) => {
  const [content, setContent] = React.useState('');
  const [hasUnsavedChanges, setHasUnsavedChanges] = React.useState(false);
  const lastSavedContentRef = React.useRef('');

  React.useEffect(() => {
    if (research) {
      setContent(research.content);
      lastSavedContentRef.current = research.content;
      setHasUnsavedChanges(false);
    }
  }, [research]);

  const handleSave = async () => {
    await onSave?.({ id: research.id, content });
    lastSavedContentRef.current = content;
    setHasUnsavedChanges(false);
  };

  const handleContentChange = (newContent) => {
    setContent(newContent);
    setHasUnsavedChanges(newContent !== lastSavedContentRef.current);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-[90vw] h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>
            Review Research for "{research?.suggestion?.title}"
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          <RichTextEditor
            content={content}
            onChange={handleContentChange}
          />
        </div>

        <DialogFooter className="mt-4">
          <div className="flex justify-between w-full">
            <div className="space-x-2">
              <div className="flex items-center gap-2">
                <Button
                  variant="default"
                  onClick={handleSave}
                  disabled={!hasUnsavedChanges}
                >
                  Save Changes
                </Button>
                {hasUnsavedChanges && (
                  <span className="text-sm text-muted-foreground">
                    * You have unsaved changes
                  </span>
                )}
              </div>
            </div>
            <div className="space-x-2">
              <Button
                variant="outline"
                onClick={onClose}
              >
                Close
              </Button>
              {research?.status !== 'APPROVED' && !hasArticle && (
                <Button
                  variant="default"
                  className="bg-green-600 hover:bg-green-700"
                  onClick={() => onApprove?.(research.id)}
                  disabled={hasUnsavedChanges}
                >
                  Approve
                </Button>
              )}
              {(research?.status === 'APPROVED' || research?.status === 'REJECTED') && !hasArticle && (
                <Button
                  variant="secondary"
                  onClick={() => onMakePending?.(research.id)}
                  disabled={hasUnsavedChanges}
                >
                  Make Pending
                </Button>
              )}
              {research?.status !== 'REJECTED' &&  !hasArticle && (
                <Button
                  variant="destructive"
                  onClick={() => onReject?.(research.id)}
                  disabled={hasUnsavedChanges}
                >
                  Reject
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
