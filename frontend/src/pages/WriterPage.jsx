import React from 'react';
import { useToast } from "@/components/ui/use-toast";
import DataTable from '@/components/shared/DataTable';
import ContentStatus from '@/components/shared/ContentStatus';
import ConfirmationDialog from '@/components/shared/ConfirmationDialog';
import GenerationDialog from '@/components/shared/GenerationDialog';
import { contentService } from '@/services/content';
import { ArticleEditor, GenerateDYKDialog } from '@/components/ArticleComponents';

export const WriterPage = () => {
  const { toast } = useToast();

  // Data state
  const [articles, setArticles] = React.useState([]);
  const [tags, setTags] = React.useState([]);

  // UI state
  const [loading, setLoading] = React.useState(true);
  const [editingArticle, setEditingArticle] = React.useState(null);
  const [generationInProgress, setGenerationInProgress] = React.useState(false);
  const [confirmDialog, setConfirmDialog] = React.useState({
    open: false,
    title: '',
    description: '',
    action: null,
  });
  const [selectedArticleId, setSelectedArticleId] = React.useState(null);
  const [dykDialogOpen, setDykDialogOpen] = React.useState(false);

  // Filtering, Sorting & Pagination state
  const [statusFilter, setStatusFilter] = React.useState('ALL');
  const [globalFilter, setGlobalFilter] = React.useState('');
  const [sorting, setSorting] = React.useState([]); // e.g. [{ id: 'title', desc: false }]
  const [currentPage, setCurrentPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const pageSize = 12;

  // Fetch articles with pagination, sorting, filtering
  const fetchArticles = async () => {
    try {
      setLoading(true);
      const sortParam = sorting[0]?.id || 'title';
      const direction = sorting[0]?.desc ? 'desc' : 'asc';
      // Assumes contentService.getArticles now accepts these parameters
      const data = await contentService.getArticles(
        currentPage,
        pageSize,
        statusFilter === 'ALL' ? null : statusFilter,
        globalFilter,
        sortParam,
        direction
      );
      // Assume the response is { articles: [...], pages: number }
      // noinspection JSUnresolvedReference
      setArticles(data.articles || []);
      setTotalPages(data.pages || 1);
    } catch (error) {
      console.error("Error fetching articles:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load articles. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch tags for article metadata (only approved tags)
  const fetchTags = async () => {
    try {
      const data = await contentService.getAllTags('APPROVED');
      setTags(data || []);
    } catch (error) {
      console.error("Error fetching tags:", error);
    }
  };


  // Re-fetch articles whenever any filter/sort/pagination state changes
  React.useEffect(() => {
    (async () => {
      await fetchArticles();
    })();
  }, [globalFilter, statusFilter, sorting, currentPage]);

  // Fetch tags on mount
  React.useEffect(() => {
    (async () => {
      await fetchTags();
    })();
  }, []);

  // Handler for updating (saving) an article from the editor
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
      console.log("Error updating article:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update article. Please try again.",
      });
    }
  };

  // Handler for updating article status
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
      console.log("Error updating article status:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: `Failed to update article status. Please try again.`,
      });
    }
  };

  // Handler for generating a story promotion
  const handleGenerateStory = async (articleId) => {
    try {
      const { success, message } = await contentService.generateStoryPromotion(articleId);
      setGenerationInProgress(true);
      if (success) {
        toast({
          title: "Success",
          description: message,
        });
      } else {
        toast({
          variant: "destructive",
          title: "Error",
          description: message,
        });
      }
    } catch (error) {
      console.log("Error generating story promotion:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to start story generation. Please try again.",
      });
    }
  };

  // Handler for generating DYK posts
  const handleGenerateDidYouKnow = async (articleId, count) => {
    try {
      const { success, message } = await contentService.generateDidYouKnowPosts(articleId, count);
      setGenerationInProgress(true);
      if (success) {
        toast({
          title: "Success",
          description: message,
        });
      } else {
        toast({
          variant: "destructive",
          title: "Error",
          description: message,
        });
      }
    } catch (error) {
      console.log("Error generating DYK posts:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to start posts generation. Please try again.",
      });
    }
  };

  // Helper to show the confirmation dialog
  const showConfirmDialog = (title, description, action) => {
    setConfirmDialog({
      open: true,
      title,
      description,
      action,
    });
  };

  // Define the row-level actions for articles
  const articleActions = [
    {
      label: "Review Article",
      onClick: (article) => setEditingArticle(article),
      shouldShow: () => true,
    },
    {
      label: "Approve",
      onClick: (article) =>
        showConfirmDialog(
          "Approve Article",
          "Are you sure you want to approve this article?",
          () => handleUpdateStatus(article.id, 'APPROVED')
        ),
      shouldShow: (article) => article.status !== 'APPROVED',
    },
    {
      label: "Reject",
      onClick: (article) =>
        showConfirmDialog(
          "Reject Article",
          "Are you sure you want to reject this article?",
          () => handleUpdateStatus(article.id, 'REJECTED')
        ),
      shouldShow: (article) => article.status !== 'REJECTED',
    },
    {
      label: "Make Pending",
      onClick: (article) =>
        showConfirmDialog(
          "Make Pending",
          "Are you sure you want to set this article back to pending status?",
          () => handleUpdateStatus(article.id, 'PENDING')
        ),
      shouldShow: (article) =>
        article.status === 'APPROVED' || article.status === 'REJECTED',
    },
    {
      label: "Generate Story",
      onClick: (article) =>
        showConfirmDialog(
          "Generate Story",
          "Are you sure you want to generate a story promotion for this article?",
          () => handleGenerateStory(article.id)
        ),
      shouldShow: (article) => article.status === 'APPROVED',
    },
    {
      label: "Generate DYK Posts",
      onClick: (article) => {
        setSelectedArticleId(article.id);
        setDykDialogOpen(true);
      },
      shouldShow: (article) => article.status === 'APPROVED',
    },
  ];

  // Configure columns for DataTable.
  const columnsOrder = ['title', 'status', 'tags'];
  const columnsOverride = [
    {
      accessorKey: 'title',
      header: 'Title',
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => <ContentStatus status={row.getValue('status')} />,
    },
    {
      accessorKey: 'tags',
      header: 'Tags',
      cell: ({ row }) => {
        const tags = row.getValue('tags') || [];
        return (
          <div className="flex flex-wrap gap-1">
            {tags.map(tag => (
              <span
                key={tag.id}
                className="px-2 py-1 text-xs rounded-full bg-secondary text-secondary-foreground"
              >
                {tag.name}
              </span>
            ))}
          </div>
        );
      },
    },
  ];
  const columnWidths = {
    status: 'w-[500px]',
    actions: 'w-[100px]',
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Writer Dashboard</h1>
      </div>

      <DataTable
        data={articles}
        loading={loading}
        actions={articleActions}
        // Server‑side pagination & sorting
        pageCount={totalPages}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        sorting={sorting}
        setSorting={setSorting}
        globalFilter={globalFilter}
        setGlobalFilter={setGlobalFilter}
        // Filters
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        showStatusFilter={true}
        // Column configuration
        columnsOrder={columnsOrder}
        columnsOverride={columnsOverride}
        columnWidths={columnWidths}
        pageSize={pageSize}
      />

      {editingArticle && (
        <ArticleEditor
          article={editingArticle}
          isOpen={!!editingArticle}
          onClose={() => setEditingArticle(null)}
          onSave={handleUpdateArticle}
          onApprove={(id) => handleUpdateStatus(id, 'APPROVED')}
          onReject={(id) => handleUpdateStatus(id, 'REJECTED')}
          onMakePending={(id) =>
            showConfirmDialog(
              "Make Pending",
              "Are you sure you want to set this article back to pending status?",
              () => handleUpdateStatus(id, 'PENDING')
            )
          }
          onGenerateStory={handleGenerateStory}
          onGenerateDidYouKnow={handleGenerateDidYouKnow}
          tags={tags}
        />
      )}

      <ConfirmationDialog
        open={confirmDialog.open}
        title={confirmDialog.title}
        description={confirmDialog.description}
        onConfirm={() => {
          confirmDialog.action?.();
          setConfirmDialog({
            open: false,
            title: '',
            description: '',
            action: null,
          });
        }}
        onClose={() =>
          setConfirmDialog({
            open: false,
            title: '',
            description: '',
            action: null,
          })
        }
      />

      <GenerationDialog
        open={generationInProgress}
        onOpenChange={(open) => {
          if (!open) setGenerationInProgress(false);
        }}
        resource="Content"
      />

      <GenerateDYKDialog
        isOpen={dykDialogOpen}
        onClose={() => {
          setDykDialogOpen(false);
          setSelectedArticleId(null);
        }}
        onGenerate={handleGenerateDidYouKnow}
      />
    </div>
  );
};
