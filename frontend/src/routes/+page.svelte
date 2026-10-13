<script lang="ts">
	let file = $state<File | null>(null);
	let loading = $state(false);
	let isDragging = $state(false); // Track drag state

	let invoiceData = $state<any>(null);
	let needsReview = $state<boolean>(false);
	let routingMessage = $state<string>('');

	let isSubmitDisabled = $derived(!file || loading);

	function handleFileChange(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			file = target.files[0];
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		isDragging = true;
	}

	function handleDragLeave() {
		isDragging = false;
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		isDragging = false;
		if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
			file = event.dataTransfer.files[0];
		}
	}

	async function uploadInvoice(event: Event) {
		event.preventDefault();
		if (!file) return;

		loading = true;
		invoiceData = null; // Clear previous results

		const formData = new FormData();
		formData.append('file', file);

		try {
			const response = await fetch('/api/extract', {
				method: 'POST',
				body: formData
			});

			if (!response.ok) throw new Error('Server returned an error');

			const result = await response.json();
			invoiceData = result.data;
			needsReview = result.needs_review ?? true;
			routingMessage = result.routing_message || 'System Error: Validation bypassed.';
		} catch (error) {
			console.error('Upload failed:', error);
			alert('Failed to extract data. Is the FastAPI server running?');
		} finally {
			loading = false;
		}
	}
</script>

<main class="min-h-screen bg-gray-50 p-8">
	<div class="mx-auto max-w-3xl space-y-8">
		<div class="border-b border-gray-200 pb-5">
			<h1 class="text-3xl font-bold text-gray-900">Multimodal Invoice Agent</h1>
			<p class="mt-2 text-sm text-gray-500">
				Upload a vendor invoice to automatically extract and verify details against the ERP system.
			</p>
		</div>

		<!-- Upload Form with Drag & Drop -->
		<form onsubmit={uploadInvoice} class="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
			<div class="space-y-6">
				<label
					for="dropzone-file"
					ondragover={handleDragOver}
					ondragleave={handleDragLeave}
					ondrop={handleDrop}
					class="flex cursor-pointer justify-center rounded-lg border-2 px-6 py-10 transition-all duration-200
            {isDragging
						? 'scale-[1.02] border-dotted border-blue-500 bg-blue-50 ring-4 ring-blue-50'
						: 'border-dashed border-gray-300 hover:border-blue-400 hover:bg-gray-50'}"
				>
					<div class="text-center">
						<!-- Icon -->
						<svg
							class="mx-auto h-12 w-12 text-gray-300"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
							aria-hidden="true"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="1.5"
								d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
							/>
						</svg>

						<!-- Text -->
						<div class="mt-4 flex justify-center text-sm leading-6 text-gray-600">
							<span class="pl-1">Upload a file or drag and drop</span>
						</div>
						<p class="mt-1 text-xs leading-5 text-gray-500">PDF up to 10MB</p>
					</div>

					<!-- The Input -->
					<input
						id="dropzone-file"
						type="file"
						accept=".pdf"
						onchange={handleFileChange}
						class="hidden"
					/>
				</label>

				{#if file}
					<div
						class="flex items-center rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-gray-700 shadow-sm"
					>
						<!-- New File SVG Icon -->
						<svg
							class="mr-3 h-6 w-6 shrink-0 text-blue-500"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
							></path>
						</svg>

						<span class="truncate font-medium">{file.name}</span>
						<button
							type="button"
							class="ml-auto cursor-pointer text-gray-400 transition-colors hover:text-red-600"
							onclick={() => (file = null)}
						>
							✕
						</button>
					</div>
				{/if}

				<button
					type="submit"
					disabled={isSubmitDisabled}
					class="w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 font-medium text-white shadow-sm transition-all hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
				>
					{loading ? 'Executing Agentic Loop...' : 'Extract Data'}
				</button>
			</div>
		</form>

		<!-- Skeleton Loading State -->
		{#if loading}
			<div class="animate-pulse space-y-4 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
				<div class="h-4 w-1/4 rounded bg-gray-200"></div>
				<div class="h-10 w-full rounded bg-gray-200"></div>
				<div class="mt-4 space-y-2">
					<div class="h-4 w-full rounded bg-gray-200"></div>
					<div class="h-4 w-5/6 rounded bg-gray-200"></div>
					<div class="h-4 w-4/6 rounded bg-gray-200"></div>
				</div>
				<div class="mt-4 animate-bounce text-sm font-medium text-blue-600">
					Agent is parsing document and querying mock ERP...
				</div>
			</div>
		{/if}

		<!-- Final Results Output -->
		{#if invoiceData && !loading}
			<div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
				<h2 class="mb-4 text-xl font-semibold">Verification Results</h2>

				<div
					class="mb-6 rounded-md border p-4 {needsReview
						? 'border-red-200 bg-red-50'
						: 'border-green-200 bg-green-50'}"
				>
					<div class="flex items-center space-x-3">
						<span
							class="h-3 w-3 flex-shrink-0 rounded-full {needsReview
								? 'bg-red-600'
								: 'bg-green-600'}"
						></span>
						<div>
							<h3 class="text-sm font-medium {needsReview ? 'text-red-800' : 'text-green-800'}">
								{needsReview ? 'Human Review Required' : 'Automated Verification Passed'}
							</h3>
							<p class="mt-1 text-sm {needsReview ? 'text-red-700' : 'text-green-700'}">
								{routingMessage}
							</p>
						</div>
					</div>
				</div>

				<!-- Enterprise Data Table -->
				<div class="mt-8">
					<div class="mb-4 flex items-end justify-between">
						<div>
							<h4 class="text-sm font-semibold tracking-wider text-gray-500 uppercase">
								Vendor Details
							</h4>
							<p class="text-lg font-medium text-gray-900">{invoiceData.vendor_name}</p>
						</div>
						<div class="text-right">
							<h4 class="text-sm font-semibold tracking-wider text-gray-500 uppercase">
								Total Amount
							</h4>
							<p class="text-2xl font-bold text-gray-900">{invoiceData.total_amount} AED</p>
						</div>
					</div>

					<div class="ring-opacity-5 overflow-hidden rounded-lg shadow ring-1 ring-black">
						<table class="min-w-full divide-y divide-gray-300">
							<thead class="bg-gray-50">
								<tr>
									<th
										scope="col"
										class="py-3.5 pr-3 pl-4 text-left text-sm font-semibold text-gray-900 sm:pl-6"
										>Description</th
									>
									<th scope="col" class="px-3 py-3.5 text-right text-sm font-semibold text-gray-900"
										>Qty</th
									>
									<th scope="col" class="px-3 py-3.5 text-right text-sm font-semibold text-gray-900"
										>Unit Price</th
									>
									<th scope="col" class="px-3 py-3.5 text-right text-sm font-semibold text-gray-900"
										>Total</th
									>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-200 bg-white">
								{#each invoiceData.line_items as item}
									<tr>
										<td
											class="py-4 pr-3 pl-4 text-sm font-medium whitespace-nowrap text-gray-900 sm:pl-6"
											>{item.description}</td
										>
										<td class="px-3 py-4 text-right text-sm whitespace-nowrap text-gray-500"
											>{item.quantity}</td
										>
										<td class="px-3 py-4 text-right text-sm whitespace-nowrap text-gray-500"
											>{item.unit_price} AED</td
										>
										<td
											class="px-3 py-4 text-right text-sm font-medium whitespace-nowrap text-gray-900"
											>{item.total} AED</td
										>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			</div>
		{/if}
	</div>
</main>
