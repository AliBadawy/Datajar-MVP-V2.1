/**
 * Utility functions for the application
 */

/**
 * Format a date string to a localized date
 * @param dateString - The date string to format
 * @returns Formatted date string
 */
export function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString();
}
