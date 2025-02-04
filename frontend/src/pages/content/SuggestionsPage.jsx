/**
 * @typedef {Object} SuggestionsResponse
 * @property {Array} suggestions - The list of suggestion objects.
 * @property {number} total - The total number of suggestions.
 * @property {number} pages - The total number of pages.
 * @property {number} currentPage - The current page number.
 */

import React from "react";
import { Plus, BookOpen, ArrowUpDown } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import {
  GenerateSuggestionsDialog,
  SuggestionDialog,
} from "@/components/content/SuggestionComponents";
import DataTable from "@/components/shared/DataTable";
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";
import StepStatus from "@/components/shared/StepStatus";
import GenerationDialog from "@/components/shared/GenerationDialog";
import { contentService } from "@/services/content";
import { RecordStatus } from "@/components/shared/RecordStatus";
import { api } from "@/services/api";

export const SuggestionsPage = () => {
  const { toast } = useToast();

  // DATA
  const [suggestions, setSuggestions] = React.useState([]);
  const [taxonomies, setTaxonomies] = React.useState([]);

  // UI STATES
  const [loading, setLoading] = React.useState(true);
  const [editingSuggestion, setEditingSuggestion] = React.useState(null);
  const [generatingSuggestions, setGeneratingSuggestions] = React.useState(false);
  const [generationInProgress, setGenerationInProgress] = React.useState(false);

  // Filter / Sorting / Pagination
  const [globalFilter, setGlobalFilter] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState("ALL");
  const [taxonomyFilter, setTaxonomyFilter] = React.useState(null);
  const [categoryFilter, setCategoryFilter] = React.useState(null);
  const [sorting, setSorting] = React.useState([]); // e.g. [ {id: 'title', desc: false} ]
  const [currentPage, setCurrentPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const pageSize = 10;
  const showStatusFilter = true;

  // Confirmation dialog
  const [confirmDialog, setConfirmDialog] = React.useState({
    open: false,
    title: "",
    description: "",
    action: null,
  });

  React.useEffect(() => {
    (async () => {
      try {
        await fetchSuggestions();
      } catch (err) {
        console.error("Error fetching suggestions:", err);
      }

      try {
        await fetchTaxonomies();
      } catch (err) {
        console.error("Error fetching taxonomies:", err);
      }
    })();
  }, [globalFilter, statusFilter, sorting, currentPage, categoryFilter]);

  async function fetchSuggestions() {
    try {
      setLoading(true);
      const sortParam = sorting[0]?.id || "id";
      // noinspection JSUnresolvedReference
      const direction = sorting[0]?.asc ? "asc" : "desc";

      const data = await contentService.getSuggestions(
        currentPage,
        pageSize,
        statusFilter === "ALL" ? null : statusFilter,
        globalFilter,
        sortParam,
        direction,
        categoryFilter,
      );

      setSuggestions(data.suggestions || []);
      setTotalPages(data.pages);
    } catch (error) {
      console.error("Error fetching suggestions:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load suggestions.",
      });
    } finally {
      setLoading(false);
    }
  }

  const fetchTaxonomies = async () => {
    try {
      const data = await contentService.getTaxonomies();
      setTaxonomies(data || []);
    } catch (error) {
      console.error("Error fetching taxonomies:", error);
    }
  };

  const handleGenerateSuggestions = async (data) => {
    try {
      const mutationData = {
        categoryId: parseInt(data.categoryId, 10),
        count: parseInt(data.count, 10),
      };
      const { success, message } = await contentService.generateSuggestions(
        mutationData
      );

      setGeneratingSuggestions(false);
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
      console.error("Error generating suggestions:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to generate suggestions. Please try again.",
      });
    }
  };

  const handleUpdateSuggestion = async (suggestionData) => {
    try {
      await contentService.updateSuggestion(suggestionData.id, suggestionData);
      toast({
        title: "Success",
        description: "Suggestion updated successfully",
      });
      setEditingSuggestion(null);
      await fetchSuggestions();
    } catch (error) {
      console.error("Error updating suggestion:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update suggestion. Please try again.",
      });
    }
  };

  const handleUpdateStatus = async (suggestion, newStatus) => {
    try {
      await contentService.updateSuggestionStatus(suggestion.id, newStatus);
      toast({
        title: "Success",
        description: `Suggestion ${newStatus.toLowerCase()} successfully`,
      });
      await fetchSuggestions();
    } catch (error) {
      console.error("Error updating the suggestion status:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update suggestion status. Please try again.",
      });
    }
  };

  const handleGenerateResearch = async (suggestion) => {
    try {
      const { success, message } = await contentService.generateResearch(
        suggestion.id
      );
      toast({
        variant: "success",
        title: "Research generation started",
        description: message,
      });
      if (!success) {
        toast({
          variant: "destructive",
          title: "Error",
          description: message,
        });
      }
    } catch (error) {
      console.error("Error generating research:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to start research generation. Please try again.",
      });
    }
  };

  const handleBulkGenerateArticles = async () => {
    try {
      const { status, job_id, queue_position } = await api.bulkGenerateArticles();

      toast({
        variant: "success",
        title: "Bulk generation started",
        description: `Job ID: ${job_id}, Position: ${queue_position}, Status: ${status}`,
      });

      await fetchSuggestions();
    } catch (error) {
      console.error("Error bulk generating articles:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: error.message || "Failed to bulk generate articles. Please try again.",
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

  // Context menu actions for each suggestion
  const suggestionActions = [
    {
      label: "Edit Suggestion",
      onClick: (sug) => setEditingSuggestion(sug),
      shouldShow: () => true,
    },
    {
      label: "Generate Research",
      onClick: (sug) =>
        showConfirmDialog(
          "Generate Research",
          `Generate research for "${sug.title}"?`,
          () => handleGenerateResearch(sug)
        ),
      shouldShow: (sug) => sug.status === "APPROVED" && !sug.research,
    },
    {
      label: "Approve",
      onClick: (sug) =>
        showConfirmDialog(
          "Approve Suggestion",
          `Mark "${sug.title}" as approved?`,
          () => handleUpdateStatus(sug, "APPROVED")
        ),
      shouldShow: (sug) => sug.status !== "APPROVED",
    },
    {
      label: "Reject",
      onClick: (sug) =>
        showConfirmDialog(
          "Reject Suggestion",
          `Mark "${sug.title}" as rejected?`,
          () => handleUpdateStatus(sug, "REJECTED")
        ),
      shouldShow: (sug) => sug.status !== "REJECTED" && !sug.research,
    },
    {
      label: "Make Pending",
      onClick: (sug) =>
        showConfirmDialog(
          "Make Pending",
          `Mark "${sug.title}" as pending?`,
          () => handleUpdateStatus(sug, "PENDING")
        ),
      shouldShow: (sug) =>
        (sug.status === "APPROVED" || sug.status === "REJECTED") && !sug.research,
    },
  ];

  // Custom cell renderer for the status column
  const columnsOrder = ["id", "title", "status", "researchCompleted"];
  const columnsOverride = [
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => <RecordStatus value={row.getValue("status")} />,
    },
    {
      id: "researchCompleted",
      accessorKey: "researchCompleted",
      header: () => (
        <Button
          variant="ghost"
          className="hover:bg-transparent focus:bg-transparent px-0"
          onClick={() =>
            setSorting((prev) => {
              const existingSort = prev.find((s) => s.id === "researchCompleted");
              if (!existingSort) {
                return [{ id: "researchCompleted", desc: false }];
              }
              return [{ id: "researchCompleted", desc: !existingSort.desc }];
            })
          }
        >
          Research Completed
          <ArrowUpDown className="ml-2 h-4 w-4 transition-transform hover:scale-110" />
        </Button>
      ),
      cell: ({ row }) => {
        // If research exists, then the step is considered completed.
        const suggestion = row.original;
        const done = Boolean(suggestion.research);
        return <StepStatus done={done} />;
      },
    },
  ];
  const columnWidths = {
    id: "w-[100px]",
    status: "w-[250px]",
    researchCompleted: "w-[250px]",
    actions: "w-[100px]",
  };

  // Compute the number of approved suggestions without research
  const approvedWithoutResearchCount = React.useMemo(() => {
    return suggestions.filter(sug => sug.status === "APPROVED" && !sug.research).length;
  }, [suggestions]);

  // Control buttons (now with two buttons)
  const controlButtons = [
    <Button key="generate" onClick={() => setGeneratingSuggestions(true)}>
      <Plus className="h-4 w-4 mr-2" />
      Generate Suggestions
    </Button>,
    <Button
      key="bulk-generate"
      onClick={() =>
        showConfirmDialog(
          "Bulk Generate Articles",
          `This will schedule a job to generate articles for ${approvedWithoutResearchCount} approved suggestions.`,
          handleBulkGenerateArticles
        )
      }
      disabled={approvedWithoutResearchCount === 0}
    >
      <BookOpen className="h-4 w-4 mr-2" />
      Bulk Generate Articles
    </Button>,
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Article Suggestions</h1>
      </div>

      {/* DataTable usage */}
      <DataTable
        data={suggestions}
        loading={loading}
        actions={suggestionActions}
        // server-side pagination & sorting
        pageCount={totalPages}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        sorting={sorting}
        setSorting={setSorting}
        // filters
        globalFilter={globalFilter}
        setGlobalFilter={setGlobalFilter}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        showCategoryFilter={true}
        taxonomies={taxonomies}
        taxonomyFilter={taxonomyFilter}
        setTaxonomyFilter={setTaxonomyFilter}
        categoryFilter={categoryFilter}
        setCategoryFilter={setCategoryFilter}
        // optional overrides
        columnsOrder={columnsOrder}
        columnsOverride={columnsOverride}
        columnWidths={columnWidths}
        pageSize={pageSize}
        showStatusFilter={showStatusFilter}
        controlButtons={controlButtons}
      />

      {/* Generate Suggestions Dialog */}
      <GenerateSuggestionsDialog
        isOpen={generatingSuggestions}
        onClose={() => setGeneratingSuggestions(false)}
        onGenerate={handleGenerateSuggestions}
        taxonomies={taxonomies}
      />

      {/* Edit dialog */}
      <SuggestionDialog
        suggestion={editingSuggestion}
        isOpen={!!editingSuggestion}
        onClose={() => setEditingSuggestion(null)}
        onSave={handleUpdateSuggestion}
        onChangeStatus={handleUpdateStatus}
      />

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        open={confirmDialog.open}
        title={confirmDialog.title}
        description={confirmDialog.description}
        onConfirm={confirmDialog.action}
        onClose={() =>
          setConfirmDialog({ open: false, title: "", description: "", action: null })
        }
      />

      {/* Generation In Progress Dialog */}
      <GenerationDialog
        open={generationInProgress}
        onOpenChange={(open) => {
          // When the dialog is closed, update the state
          if (!open) setGenerationInProgress(false);
        }}
        resource="Suggestions"
      />
    </div>
  );
};
