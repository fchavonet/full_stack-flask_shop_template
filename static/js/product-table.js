/*****************
 * INLINE SEARCH *
 *****************/

// Get search input and all table rows.
const tableSearch = document.getElementById("table-search");
const rows = document.querySelectorAll("#products-table tbody tr");

// Listen for input events on search field.
tableSearch.addEventListener("input", function () {
	const filter = this.value.trim().toLowerCase();

	// Show or hide each row based on whether it contains the filter text.
	rows.forEach(function (row) {
		const text = row.textContent.toLowerCase();

		if (text.indexOf(filter) !== -1) {
			row.style.display = "";
		} else {
			row.style.display = "none";
		}
	});
});


/*****************
 * TABLE SORTING *
 *****************/

// Get the table and its header cells.
const productsTable = document.getElementById("products-table");
const headers = productsTable.querySelectorAll("th");

// Attach click handler to each header for sorting.
headers.forEach(function (th, index) {
	th.style.cursor = "pointer";

	// Track first click and sort direction.
	let isFirstClick = true;
	let ascending = false;

	th.addEventListener("click", function () {
		const tbody = productsTable.tBodies[0];
		const currentRows = Array.from(tbody.querySelectorAll("tr"));

		// On first click: simply reverse the current row order.
		if (isFirstClick) {
			const reversedRows = currentRows.slice();
			reversedRows.reverse();

			reversedRows.forEach(function (row) {
				tbody.appendChild(row);
			});

			isFirstClick = false;
			return;
		}

		// On subsequent clicks: toggle sort direction then sort.
		ascending = !ascending;
		const sortedRows = currentRows.slice();

		sortedRows.sort(function (a, b) {
			const cellA = a.cells[index].innerText.trim();
			const cellB = b.cells[index].innerText.trim();

			// Attempt numeric comparison by stripping non-digits
			const numA = parseFloat(cellA.replace(/[€\s,]/g, ""));
			const numB = parseFloat(cellB.replace(/[€\s,]/g, ""));

			if (!isNaN(numA) && !isNaN(numB)) {
				// Numeric sort.
				if (ascending) {
					return numA - numB;
				} else {
					return numB - numA;
				}
			}

			// Fallback to string comparison.
			if (ascending) {
				return cellA.localeCompare(cellB);
			} else {
				return cellB.localeCompare(cellA);
			}
		});

		// Re-append rows in sorted order.
		sortedRows.forEach(function (row) {
			tbody.appendChild(row);
		});
	});
});
