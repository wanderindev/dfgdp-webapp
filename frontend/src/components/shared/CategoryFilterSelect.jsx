import React from "react";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";

/**
 * CategoryFilterSelect renders two dropdowns:
 * - A taxonomy select that lists all taxonomies.
 * - A category select that lists the categories for the selected taxonomy.
 *
 * @param {object} props
 * @param {Array} props.taxonomies - Array of taxonomies. Each taxonomy should include its categories.
 * @param {string} props.taxonomyFilter - The currently selected taxonomy ID.
 * @param {Function} props.setTaxonomyFilter - Callback to update the taxonomy selection.
 * @param {string} props.categoryFilter - The currently selected category ID.
 * @param {Function} props.setCategoryFilter - Callback to update the category selection.
 *
 * @returns {JSX.Element}
 */
function CategoryFilterSelect({
  taxonomies,
  taxonomyFilter,
  setTaxonomyFilter,
  categoryFilter,
  setCategoryFilter,
}) {
  // Find the selected taxonomy from the provided array.
  const selectedTaxonomy = taxonomies.find((t) => t.id === taxonomyFilter);
  // If a taxonomy is selected, get its categories; otherwise, use an empty array.
  // noinspection JSUnresolvedReference
  const categories = selectedTaxonomy ? selectedTaxonomy.categories : [];

  return (
    <div className="flex items-center space-x-2">
      {/* Taxonomy Select */}
      <Select
        value={taxonomyFilter || ""}
        onValueChange={(value) => {
          setTaxonomyFilter(value);
          // Reset the category selection when taxonomy changes.
          setCategoryFilter("");
        }}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Select Taxonomy" />
        </SelectTrigger>
        <SelectContent>
          {taxonomies.map((taxonomy) => (
            <SelectItem key={taxonomy.id} value={taxonomy.id}>
              {taxonomy.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Category Select */}
      <Select
        value={categoryFilter || ""}
        onValueChange={setCategoryFilter}
        disabled={!taxonomyFilter}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Select Category" />
        </SelectTrigger>
        <SelectContent>
          {categories.map((category) => (
            <SelectItem key={category.id} value={category.id}>
              {category.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export default CategoryFilterSelect;
