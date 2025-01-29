import React from 'react';
import { useToast } from "@/components/ui/use-toast";
import { TaxonomyTree, TaxonomyDialog, CategoryDialog } from '@/components/content/TaxonomyComponents';
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
import { contentService } from "@/services/content";

export const TaxonomiesPage = () => {
  const { toast } = useToast();
  const [loading, setLoading] = React.useState(true);
  const [taxonomies, setTaxonomies] = React.useState([]);
  const [editingTaxonomy, setEditingTaxonomy] = React.useState(null);
  const [editingCategory, setEditingCategory] = React.useState(null);
  const [selectedTaxonomyId, setSelectedTaxonomyId] = React.useState(null);
  const [confirmDialog, setConfirmDialog] = React.useState({
    open: false,
    title: '',
    description: '',
    action: null,
  });

  // Fetch taxonomies on mount
  React.useEffect(() => {
    (async () => {
      try {
        await fetchTaxonomies()
      } catch (error) {
        console.error("Something went wrong:", error);
      }
    })();
  }, []);

  const fetchTaxonomies = async () => {
    try {
      setLoading(true);
      const data = await contentService.getTaxonomies();
      setTaxonomies(data);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load taxonomies. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTaxonomy = async (taxonomyData) => {
    try {
      if (taxonomyData.id) {
        await contentService.updateTaxonomy(taxonomyData.id, taxonomyData);
      } else {
        await contentService.createTaxonomy(taxonomyData);
      }
      toast({
        title: "Success",
        description: `Taxonomy ${taxonomyData.id ? 'updated' : 'created'} successfully`,
      });
      setEditingTaxonomy(null);
      await fetchTaxonomies();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: `Failed to ${taxonomyData.id ? 'update' : 'create'} taxonomy. Please try again.`,
      });
    }
  };

  const handleDeleteTaxonomy = async (taxonomyId) => {
    try {
      await contentService.deleteTaxonomy(taxonomyId);
      toast({
        title: "Success",
        description: "Taxonomy deleted successfully",
      });
      await fetchTaxonomies();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to delete taxonomy. Please try again.",
      });
    }
  };

  const handleSaveCategory = async (categoryData) => {
    try {
      if (categoryData.id) {
        await contentService.updateCategory(categoryData.id, categoryData);
      } else {
        await contentService.createCategory(categoryData);
      }
      toast({
        title: "Success",
        description: `Category ${categoryData.id ? 'updated' : 'created'} successfully`,
      });
      setEditingCategory(null);
      setSelectedTaxonomyId(null);
      await fetchTaxonomies();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: `Failed to ${categoryData.id ? 'update' : 'create'} category. Please try again.`,
      });
    }
  };

  const handleDeleteCategory = async (categoryId) => {
    try {
      await contentService.deleteCategory(categoryId);
      toast({
        title: "Success",
        description: "Category deleted successfully",
      });
      await fetchTaxonomies();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to delete category. Please try again.",
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

  if (loading && !taxonomies.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Taxonomies & Categories</h1>

      <TaxonomyTree
        taxonomies={taxonomies}
        onAddTaxonomy={() => setEditingTaxonomy({})}
        onEditTaxonomy={setEditingTaxonomy}
        onDeleteTaxonomy={(id) => showConfirmDialog(
          "Delete Taxonomy",
          "Are you sure you want to delete this taxonomy? This will also delete all associated categories.",
          () => handleDeleteTaxonomy(id)
        )}
        onAddCategory={(taxonomyId) => {
          setSelectedTaxonomyId(taxonomyId);
          setEditingCategory({});
        }}
        onEditCategory={setEditingCategory}
        onDeleteCategory={(id) => showConfirmDialog(
          "Delete Category",
          "Are you sure you want to delete this category?",
          () => handleDeleteCategory(id)
        )}
      />

      <TaxonomyDialog
        taxonomy={editingTaxonomy}
        isOpen={!!editingTaxonomy}
        onClose={() => setEditingTaxonomy(null)}
        onSave={handleSaveTaxonomy}
      />

      <CategoryDialog
        category={editingCategory}
        taxonomyId={selectedTaxonomyId}
        isOpen={!!editingCategory}
        onClose={() => {
          setEditingCategory(null);
          setSelectedTaxonomyId(null);
        }}
        onSave={handleSaveCategory}
      />

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
    </div>
  );
};
