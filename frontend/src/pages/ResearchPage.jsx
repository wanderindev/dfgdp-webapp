import React from 'react';
import { useToast } from "@/components/ui/use-toast";
import { ResearchTable, ResearchReviewDialog } from '@/components/content/ResearchComponents';
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { contentService } from '@/services/content';

export const ResearchPage = () => {
  const { toast } = useToast();
  const [loading, setLoading] = React.useState(true);
  const [research, setResearch] = React.useState([]);
  const [reviewingResearch, setReviewingResearch] = React.useState(null);
  const [statusFilter, setStatusFilter] = React.useState('ALL');
  const [generationInProgress, setGenerationInProgress] = React.useState(false);
  const [confirmDialog, setConfirmDialog] = React.useState({
    open: false,
    title: '',
    description: '',
    action: null,
  });

  // Fetch research items on mount and when status filter changes
  React.useEffect(() => {
    fetchResearch();
  }, [statusFilter]);

  const fetchResearch = async () => {
    try {
      setLoading(true);
      const data = await contentService.getResearch(
        statusFilter === 'ALL' ? null : statusFilter
      );
      setResearch(data || []);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load research items. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveResearch = async (researchData) => {
    try {
      await contentService.updateResearch(researchData.id, researchData);
      toast({
        title: "Success",
        description: "Changes saved successfully",
      });
      fetchResearch();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update research content. Please try again.",
      });
    }
  };

  const handleUpdateStatus = async (researchId, newStatus) => {
    try {
      await contentService.updateResearchStatus(researchId, newStatus);
      toast({
        title: "Success",
        description: `Research ${newStatus.toLowerCase()} successfully`,
      });
      setReviewingResearch(null);
      fetchResearch();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: `Failed to ${newStatus.toLowerCase()} research. Please try again.`,
      });
    }
  };

  const handleGenerateArticle = async (research) => {
    try {
      await contentService.generateArticle(research.id);
      setGenerationInProgress(true);
      toast({
        title: "Success",
        description: "Article generation started. It will be available in a few minutes.",
      });
      fetchResearch(); // Refresh to update the research item's status
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to start article generation. Please try again.",
      });
    }
  };

  const handleGenerateMedia = async (research) => {
    try {
      await contentService.generateMediaSuggestions(research.id);
      setGenerationInProgress(true);
      toast({
        title: "Success",
        description: "Media suggestions generation started. They will be available in a few minutes.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to start media suggestions generation. Please try again.",
      });
    }
  };

  const showConfirmDialog = (title, description, action) => {
    setConfirmDialog({
      open: true,
      title,
      description,
      action,
    });
  };

  const handleMakePending = async (researchId) => {
    try {
      await contentService.updateResearchStatus(researchId, 'PENDING');
      toast({
        title: "Success",
        description: "Research status set to pending",
      });
      setReviewingResearch(null);
      fetchResearch();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update research status. Please try again.",
      });
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Research Management</h1>

      <ResearchTable
        data={research}
        loading={loading}
        onReview={setReviewingResearch}
        onGenerateArticle={(research) => showConfirmDialog(
          "Generate Article",
          `Are you sure you want to generate an article for "${research.suggestion.title}"?`,
          () => handleGenerateArticle(research)
        )}
        onGenerateMedia={(research) => showConfirmDialog(
          "Generate Media",
          `Are you sure you want to generate media suggestions for "${research.suggestion.title}"?`,
          () => handleGenerateMedia(research)
        )}
        onMakePending={(researchId) => showConfirmDialog(
          "Make Pending",
          "Are you sure you want to set this research back to pending status?",
          () => handleMakePending(researchId)
        )}
        onStatusFilterChange={setStatusFilter}
        currentStatusFilter={statusFilter}
      />

      {reviewingResearch && (
        <ResearchReviewDialog
          research={reviewingResearch}
          isOpen={!!reviewingResearch}
          onClose={() => setReviewingResearch(null)}
          onSave={handleSaveResearch}
          onApprove={(id) => handleUpdateStatus(id, 'APPROVED')}
          onReject={(id) => handleUpdateStatus(id, 'REJECTED')}
          onMakePending={(id) => showConfirmDialog(
            "Make Pending",
            "Are you sure you want to set this research back to pending status?",
            () => handleMakePending(id)
          )}
        />
      )}

      <AlertDialog
        open={confirmDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setConfirmDialog({
              open: false,
              title: '',
              description: '',
              action: null,
            });
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmDialog.title}</AlertDialogTitle>
            <AlertDialogDescription>
              {confirmDialog.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => {
              confirmDialog.action();
              setConfirmDialog({
                open: false,
                title: '',
                description: '',
                action: null,
              });
            }}>
              Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog
        open={generationInProgress}
        onOpenChange={() => setGenerationInProgress(false)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generating Article</DialogTitle>
          </DialogHeader>
          <p>
            Your article is being generated and will be available in a few minutes.
            You can close this dialog and continue working.
          </p>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ResearchPage;