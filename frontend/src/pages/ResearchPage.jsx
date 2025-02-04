import React from 'react';

import { useToast } from '@/components/ui/use-toast';
import { Button } from "@/components/ui/button";
import { ArrowUpDown } from "lucide-react";
import DataTable from '@/components/shared/DataTable';
import ContentStatus from '@/components/shared/ContentStatus';
import ConfirmationDialog from '@/components/shared/ConfirmationDialog';
import GenerationDialog from '@/components/shared/GenerationDialog';
import StepStatus from "@/components/shared/StepStatus";
import { ResearchReviewDialog }from '@/components/ResearchComponents';
import { contentService } from '@/services/content';

export const ResearchPage = () => {
  const { toast } = useToast();

  // Data state
  const [research, setResearch] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [taxonomies, setTaxonomies] = React.useState([]);

  // UI states
  const [reviewingResearch, setReviewingResearch] = React.useState(null);
  const [generationInProgress, setGenerationInProgress] = React.useState(false);
  const [hasArticle, setHasArticle] = React.useState(false);
  const [confirmDialog, setConfirmDialog] = React.useState({
    open: false,
    title: '',
    description: '',
    action: null,
  });

  // Filtering, Sorting & Pagination state
  const [statusFilter, setStatusFilter] = React.useState('ALL');
  const [globalFilter, setGlobalFilter] = React.useState('');
  const [taxonomyFilter, setTaxonomyFilter] = React.useState(null);
  const [categoryFilter, setCategoryFilter] = React.useState(null)
  const [sorting, setSorting] = React.useState([]); // e.g. [{ id: 'suggestion.title', desc: false }]
  const [currentPage, setCurrentPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const pageSize = 10;

  const fetchTaxonomies = async () => {
    try {
      const data = await contentService.getTaxonomies();
      setTaxonomies(data || []);
    } catch (error) {
      console.error("Error fetching taxonomies:", error);
    }
  };

  // Fetch research items from the backend with server‑side pagination, sorting, and filtering.
  const fetchResearch = async () => {
    try {
      setLoading(true);
      const sortParam =
        sorting[0]?.id === 'suggestion.title' ? 'suggestion.title' : sorting[0]?.id || 'suggestion.title';
      const direction = sorting[0]?.desc ? 'desc' : 'asc';

      const data = await contentService.getResearch(
        currentPage,
        pageSize,
        statusFilter === 'ALL' ? null : statusFilter,
        globalFilter,
        sortParam,
        direction,
        categoryFilter,
      );

      // Transform each research record to add a `title` field equal to suggestion.title.
      const transformedResearch = (data.research || []).map(item => ({
        ...item,
        title: item.suggestion?.title || '',
      }));

      setResearch(transformedResearch);
      setTotalPages(data.pages || 1);
    } catch (error) {
      console.log('Failed to load research items', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load research items. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  };


  React.useEffect(() => {
    (async () => {
      try {
        await fetchResearch();
      } catch (err) {
        console.error("Error fetching research:", err);
      }

      try {
        await fetchTaxonomies();
      } catch (err) {
        console.error("Error fetching taxonomies:", err);
      }
    })();
  }, [globalFilter, statusFilter, sorting, currentPage, categoryFilter]);

  // Save (update) research content changes.
  const handleSaveResearch = async (researchData) => {
    try {
      await contentService.updateResearch(researchData.id, researchData);
      toast({
        title: 'Success',
        description: 'Changes saved successfully',
      });
      await fetchResearch();
    } catch (error) {
      console.log('Failed to update research content', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to update research content. Please try again.',
      });
    }
  };

  // Update research status (approve, reject, etc.)
  const handleUpdateStatus = async (researchId, newStatus, fromActions) => {
    try {
      const updatedResearch = await contentService.updateResearchStatus(researchId, newStatus);
      toast({
        title: 'Success',
        description: `Research ${newStatus.toLowerCase()} successfully`,
      });
      if (!fromActions) setReviewingResearch(updatedResearch);
      await fetchResearch();
    } catch (error) {
      console.log()
      toast({
        variant: 'destructive',
        title: 'Error',
        description: `Failed to ${newStatus.toLowerCase()} research. Please try again.`,
      });
    }
  };

  const handleGenerateArticle = async (researchItem) => {
    try {
      const { success, message } = await contentService.generateArticle(researchItem.id);
      setGenerationInProgress(true);
      if (!success) {
        toast({
          variant: 'destructive',
          title: 'Error',
          description: message,
        });
      }
      await fetchResearch();
    } catch (error) {
      console.log('Failed to start article generation', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to start article generation. Please try again.',
      });
    }
  };

  const handleGenerateMedia = async (researchItem) => {
    try {
      const { success, message } = await contentService.generateMediaSuggestions(researchItem.id);
      setGenerationInProgress(true);
      if (!success) {
        toast({
          variant: 'destructive',
          title: 'Error',
          description: message,
        });
      }
    } catch (error) {
      console.log('Failed to start media suggestions generation', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to start media suggestions generation. Please try again.',
      });
    }
  };

  const handleMakePending = async (researchId, fromActions) => {
    try {
      const updatedResearch =await contentService.updateResearchStatus(researchId, 'PENDING');
      toast({
        title: 'Success',
        description: 'Research status set to pending',
      });
      if (!fromActions) setReviewingResearch(updatedResearch);
      await fetchResearch();
    } catch (error) {
      console.log('Failed to make research pending', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to update research status. Please try again.',
      });
    }
  };

  // Helper to show the confirmation dialog.
  const showConfirmDialog = (title, description, action) => {
    setConfirmDialog({
      open: true,
      title,
      description,
      action,
    });
  };

  // Define row-level actions for each research item.
  // noinspection JSUnresolvedReference,JSUnusedLocalSymbols
  const researchActions = [
    {
      label: 'Review Research',
      onClick: (item) => {
        setReviewingResearch(item);
        // noinspection JSUnresolvedReference
        setHasArticle(item.articles && item.articles.length > 0);
      },
      shouldShow: () => true,
    },
    {
      label: "Approve",
      onClick: (item) =>
        showConfirmDialog(
          "Approve Research",
          "Are you sure you want to approve this research?",
          () => handleUpdateStatus(article.id, 'APPROVED', true)
        ),
      shouldShow: (item) => (item.status !== 'APPROVED' && (!item.articles || item.articles.length === 0)),
    },
    {
      label: "Reject",
      onClick: (item) =>
        showConfirmDialog(
          "Reject Article",
          "Are you sure you want to reject this article?",
          () => handleUpdateStatus(item.id, 'REJECTED', true)
        ),
      // Show Reject if the article is not rejected and not published.
      shouldShow: (item) => (item.status !== 'REJECTED' && (!item.articles || item.articles.length === 0)),
    },
    {
      label: 'Make Pending',
      onClick: (item) =>
        showConfirmDialog(
          'Make Pending',
          'Are you sure you want to set this research back to pending status?',
          () => handleMakePending(item.id, true)
        ),
      shouldShow: (item) =>
        (item.status === 'APPROVED' && (!item.articles || item.articles.length === 0)) ||
        (item.status === 'REJECTED' && (!item.articles || item.articles.length === 0)),
    },
    {
      label: 'Generate Article',
      onClick: (item) =>
        showConfirmDialog(
          'Generate Article',
          `Are you sure you want to generate an article for "${item.suggestion.title}"?`,
          () => handleGenerateArticle(item)
        ),
      shouldShow: (item) =>
        item.status === 'APPROVED' && (!item.articles || item.articles.length === 0),
    },
    {
      label: 'Generate Media',
      onClick: (item) =>
        showConfirmDialog(
          'Generate Media',
          `Are you sure you want to generate media suggestions for "${item.suggestion.title}"?`,
          () => handleGenerateMedia(item)
        ),
      shouldShow: (item) =>
        false, // Hide this action for now
    },
  ];


  // Configure the table: set the column order and override the status column with our custom renderer.
  const columnsOrder = ['title', 'status', 'article_completed', 'media_completed'];
  const columnsOverride = [
    {
      accessorKey: 'title',
      header: 'Article Title',
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => <ContentStatus status={row.getValue('status')} />,
    },
    {
      // New computed column for Article Completed.
      id: 'article_completed',
      accessorKey: 'article_completed',
      header: () => (
        <Button
          variant="ghost"
          className="hover:bg-transparent focus:bg-transparent px-0"
          onClick={() =>
            setSorting((prev) => {
              const existingSort = prev.find((s) => s.id === 'article_completed');
              if (!existingSort) {
                return [{ id: 'article_completed', desc: false }];
              }
              return [{ id: 'article_completed', desc: !existingSort.desc }];
            })
          }
        >
          Article Generated
          <ArrowUpDown className="ml-2 h-4 w-4 transition-transform hover:scale-110" />
        </Button>
      ),
      cell: ({ row }) => {
        // Compute if an article is completed: true if research.articles exists and has at least one item.
        const researchItem = row.original;
        // noinspection JSUnresolvedReference
        const done = researchItem.articles && researchItem.articles.length > 0;
        return <StepStatus done={done} />;
      },
    },
    {
      // New computed column for Media Completed.
      id: 'media_completed',
      accessorKey: 'media_completed',
      header: () => (
        <Button
          variant="ghost"
          className="hover:bg-transparent focus:bg-transparent px-0"
          onClick={() =>
            setSorting((prev) => {
              const existingSort = prev.find((s) => s.id === 'media_completed');
              if (!existingSort) {
                return [{ id: 'media_completed', desc: false }];
              }
              return [{ id: 'media_completed', desc: !existingSort.desc }];
            })
          }
        >
          Media Fetched
          <ArrowUpDown className="ml-2 h-4 w-4 transition-transform hover:scale-110" />
        </Button>
      ),
      cell: ({ row }) => {
        // Adjust the property name if needed.
        const researchItem = row.original;
        const done = researchItem.media && researchItem.media.length > 0;
        return <StepStatus done={done} />;
      },
    },
  ];
  const columnWidths = {
    status: 'w-[200px]',
    article_completed: 'w-[200px]',
    media_completed: 'w-[200px]',
    actions: 'w-[100px]',
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Research Management</h1>

      <DataTable
        data={research}
        loading={loading}
        actions={researchActions}
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
        showCategoryFilter={true}
        taxonomies={taxonomies}
        taxonomyFilter={taxonomyFilter}
        setTaxonomyFilter={setTaxonomyFilter}
        categoryFilter={categoryFilter}
        setCategoryFilter={setCategoryFilter}
        // Column configuration
        columnsOrder={columnsOrder}
        columnsOverride={columnsOverride}
        columnWidths={columnWidths}
        pageSize={pageSize}
      />

      {reviewingResearch && (
        <ResearchReviewDialog
          research={reviewingResearch}
          hasArticle={hasArticle}
          isOpen={!!reviewingResearch}
          onClose={() => setReviewingResearch(null)}
          onSave={handleSaveResearch}
          onApprove={(id) => handleUpdateStatus(id, 'APPROVED')}
          onReject={(id) => handleUpdateStatus(id, 'REJECTED')}
          onMakePending={(id) =>
            showConfirmDialog(
              'Make Pending',
              'Are you sure you want to set this research back to pending status?',
              () => handleMakePending(id)
            )
          }
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
        resource="Article"
      />
    </div>
  );
};
