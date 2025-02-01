import React from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";


export const GenerateSuggestionsDialog = ({
  isOpen,
  onClose,
  onGenerate,
  taxonomies = []
}) => {
  const [formData, setFormData] = React.useState({
    taxonomyId: '',
    categoryId: '',
    count: 3
  });

  const selectedTaxonomy = taxonomies.find(t => t.id.toString() === formData.taxonomyId);
  // noinspection JSUnresolvedReference
  const categories = selectedTaxonomy?.categories || [];

  const handleSubmit = (e) => {
    e.preventDefault();
    onGenerate(formData);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Generate Article Suggestions</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="taxonomy">Taxonomy</Label>
            <Select
              value={formData.taxonomyId}
              onValueChange={(value) => setFormData(prev => ({
                ...prev,
                taxonomyId: value,
                categoryId: '' // Reset category when taxonomy changes
              }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a taxonomy" />
              </SelectTrigger>
              <SelectContent>
                {taxonomies.map((taxonomy) => (
                  <SelectItem key={taxonomy.id} value={taxonomy.id.toString()}>
                    {taxonomy.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Select
              value={formData.categoryId}
              onValueChange={(value) => setFormData(prev => ({
                ...prev,
                categoryId: value
              }))}
              disabled={!formData.taxonomyId}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((category) => (
                  <SelectItem key={category.id} value={category.id.toString()}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="count">Number of Suggestions</Label>
            <Input
              id="count"
              type="number"
              min="1"
              max="15"
              value={formData.count}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                count: parseInt(e.target.value, 10)
              }))}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!formData.taxonomyId || !formData.categoryId}
            >
              Generate
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export const SuggestionDialog = ({
  suggestion,
  isOpen,
  onClose,
  onSave
}) => {
  const [formData, setFormData] = React.useState({
    title: '',
    mainTopic: '',
    pointOfView: '',
    subTopics: '',
  });

  React.useEffect(() => {
    if (suggestion) {
      setFormData({
        title: suggestion.title || '',
        mainTopic: suggestion.mainTopic || '',
        pointOfView: suggestion.pointOfView || '',
        subTopics: suggestion.subTopics?.join('\n') || '',
      });
    }
  }, [suggestion]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      id: suggestion?.id,
      ...formData,
      subTopics: formData.subTopics.split('\n').filter(Boolean),
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-[90vw] max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Edit Article Suggestion</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                title: e.target.value
              }))}
              placeholder="Enter article title"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="mainTopic">Main Topic</Label>
            <Input
              id="mainTopic"
              value={formData.mainTopic}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                mainTopic: e.target.value
              }))}
              placeholder="Enter main topic"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="subTopics">Sub Topics (one per line)</Label>
            <textarea
              id="subTopics"
              className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={formData.subTopics}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                subTopics: e.target.value
              }))}
              placeholder="Enter sub topics (one per line)"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="pointOfView">Point of View</Label>
            <Input
              id="pointOfView"
              value={formData.pointOfView}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                pointOfView: e.target.value
              }))}
              placeholder="Enter point of view"
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
