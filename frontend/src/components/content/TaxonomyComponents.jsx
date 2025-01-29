import React from 'react';
import { ChevronRight, ChevronDown, Plus, MoreHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// TaxonomyTree component for displaying the hierarchy
const TaxonomyTree = ({
  taxonomies,
  onAddTaxonomy,
  onEditTaxonomy,
  onDeleteTaxonomy,
  onAddCategory,
  onEditCategory,
  onDeleteCategory
}) => {
  const [expanded, setExpanded] = React.useState({});

  const toggleExpand = (taxonomyId) => {
    setExpanded(prev => ({
      ...prev,
      [taxonomyId]: !prev[taxonomyId]
    }));
  };

  // noinspection JSUnresolvedReference
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold">Taxonomies</h2>
        <Button onClick={onAddTaxonomy} size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Add Taxonomy
        </Button>
      </div>

      <div className="space-y-2">
        {taxonomies?.map(taxonomy => (
          <Card key={taxonomy.id}>
            <CardHeader className="py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-6 h-6 p-0 mr-2"
                    onClick={() => toggleExpand(taxonomy.id)}
                  >
                    {expanded[taxonomy.id] ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </Button>
                  <CardTitle className="text-base">{taxonomy.name}</CardTitle>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onAddCategory(taxonomy.id)}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Category
                  </Button>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onEditTaxonomy(taxonomy)}>
                        Edit Taxonomy
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-red-600"
                        onClick={() => onDeleteTaxonomy(taxonomy.id)}
                      >
                        Delete Taxonomy
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </CardHeader>
            {expanded[taxonomy.id] && (
              <CardContent>
                <div className="pl-6 space-y-2">
                  {taxonomy.categories?.map(category => (
                    <div
                      key={category.id}
                      className="flex items-center justify-between p-2 rounded-md hover:bg-accent"
                    >
                      <span>{category.name}</span>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => onEditCategory(category)}>
                            Edit Category
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => onDeleteCategory(category.id)}
                          >
                            Delete Category
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
};

// Dialog component for adding/editing taxonomies
const TaxonomyDialog = ({
  taxonomy,
  isOpen,
  onClose,
  onSave
}) => {
  const [formData, setFormData] = React.useState({
    name: '',
    description: ''
  });

  React.useEffect(() => {
    if (taxonomy) {
      setFormData({
        name: taxonomy.name,
        description: taxonomy.description
      });
    } else {
      setFormData({
        name: '',
        description: ''
      });
    }
  }, [taxonomy]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      id: taxonomy?.id,
      ...formData
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>
            {taxonomy ? 'Edit Taxonomy' : 'Add Taxonomy'}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                name: e.target.value
              }))}
              placeholder="Enter taxonomy name"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                description: e.target.value
              }))}
              placeholder="Enter taxonomy description"
              required
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">Save</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// Dialog component for adding/editing categories
const CategoryDialog = ({
  category,
  taxonomyId,
  isOpen,
  onClose,
  onSave
}) => {
  const [formData, setFormData] = React.useState({
    name: '',
    description: ''
  });

  React.useEffect(() => {
    if (category) {
      setFormData({
        name: category.name,
        description: category.description
      });
    } else {
      setFormData({
        name: '',
        description: ''
      });
    }
  }, [category]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      id: category?.id,
      taxonomyId: category?.taxonomyId || taxonomyId,
      ...formData
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>
            {category ? 'Edit Category' : 'Add Category'}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                name: e.target.value
              }))}
              placeholder="Enter category name"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                description: e.target.value
              }))}
              placeholder="Enter category description"
              required
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">Save</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export { TaxonomyTree, TaxonomyDialog, CategoryDialog };