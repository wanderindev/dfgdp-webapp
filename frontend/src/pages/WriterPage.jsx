import React from 'react';
import { useToast } from "@/components/ui/use-toast";
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
import {
  ArticlesTable,
  ArticleEditor,
} from '@/components/ArticleComponents';
import { contentService } from '@/services/content';

export const WriterPage = () => {
  const { toast } = useToast();
  const [loading, setLoading] = React.useState(true);
  const [articles, setArticles] = React.useState([]);
  const [statusFilter, setStatusFilter] = React.useState('ALL');
  const [editingArticle, setEditingArticle] = React.useState(null);
  const [tags, setTags] = React.useState([]);
  const [generationInProgress, setGenerationInProgress] = React.useState(false);
  const [confirmDialog, setConfirmDialog] = React.useState({
    open: false,
    title: '',
    description: '',
    action: null,
  });

  // Fetch articles and tags on mount and when status filter changes
  React.useEffect(() => {
    (async () => {
      try {
        await fetchArticles();
        await fetchTags();
      } catch (error) {
        console.error("Something went wrong:", error);
      }
    })();
  }, [statusFilter]);


  const fetchArticles = async () => {
    try {
      setLoading(true);
      const data = await contentService.getArticles(
        statusFilter === 'ALL' ? null : statusFilter
      );
      setArticles(data || []);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load articles. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchTags = async () => {
    try {
      const data = await contentService.getTags('APPROVED');
      setTags(data || []);
    } catch (error) {
      console.error('Error fetching tags:', error);
    }
  };

  const handleUpdateArticle = async (articleData) => {
    try {
      await contentService.updateArticle(editingArticle.id, articleData);
      toast({
        title: "Success",
        description: "Article updated successfully",
      });
      setEditingArticle(null);
      await fetchArticles();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update article. Please try again.",
      });
    }
  };

  const handleUpdateStatus = async (articleId, status) => {
    try {
      await contentService.updateArticleStatus(articleId, status);
      toast({
        title: "Success",
        description: `Article ${status.toLowerCase()} successfully`,
      });
      setEditingArticle(null);
      await fetchArticles();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: `Failed to update article status. Please try again.`,
      });
    }
  };

  const handleGenerateStory = async (articleId) => {
    try {
      await contentService.generateStoryPromotion(articleId);
      setGenerationInProgress(true);
      toast({
        title: "Success",
        description: "Story promotion generation started. It will be available in a few minutes.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to start story generation. Please try again.",
      });
    }
  };

  const handleGenerateDidYouKnow = async (articleId, count) => {
    try {
      await contentService.generateDidYouKnowPosts(articleId, count);
      setGenerationInProgress(true);
      toast({
        title: "Success",
        description: "Did You Know posts generation started. They will be available in a few minutes.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to start posts generation. Please try again.",
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

  if (loading && !articles.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Writer Dashboard</h1>
      </div>

      <ArticlesTable
        data={articles}
        loading={loading}
        onEdit={setEditingArticle}
        onApprove={(id) => showConfirmDialog(
          "Approve Article",
          "Are you sure you want to approve this article?",
          () => handleUpdateStatus(id, 'APPROVED')
        )}
        onReject={(id) => showConfirmDialog(
          "Reject Article",
          "Are you sure you want to reject this article?",
          () => handleUpdateStatus(id, 'REJECTED')
        )}
        onMakePending={(id) => showConfirmDialog(
          "Make Pending",
          "Are you sure you want to set this article back to pending status?",
          () => handleUpdateStatus(id, 'PENDING')
        )}
        onGenerateStory={(id) => showConfirmDialog(
          "Generate Story",
          "Are you sure you want to generate a story promotion for this article?",
          () => handleGenerateStory(id)
        )}
        onGenerateDidYouKnow={handleGenerateDidYouKnow}
        onStatusFilterChange={setStatusFilter}
        currentStatusFilter={statusFilter}
      />

      {editingArticle && (
        <ArticleEditor
          article={editingArticle}
          isOpen={!!editingArticle}
          onClose={() => setEditingArticle(null)}
          onSave={handleUpdateArticle}
          onApprove={(id) => handleUpdateStatus(id, 'APPROVED')}
          onReject={(id) => handleUpdateStatus(id, 'REJECTED')}
          onMakePending={(id) => showConfirmDialog(
            "Make Pending",
            "Are you sure you want to set this article back to pending status?",
            () => handleUpdateStatus(id, 'PENDING')
          )}
          onGenerateStory={handleGenerateStory}
          onGenerateDidYouKnow={handleGenerateDidYouKnow}
          tags={tags}
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
            <DialogTitle>Generating Content</DialogTitle>
          </DialogHeader>
          <p>
            Your content is being generated and will be available in a few minutes.
            You can close this dialog and continue working.
          </p>
        </DialogContent>
      </Dialog>
    </div>
  );
};
