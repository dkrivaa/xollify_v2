from pydantic import BaseModel, Field
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Optional


# Matching configuration
TOP_K_CANDIDATES = 15  # Number of candidates to send to AI
MIN_CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence to accept match


class GroceryProduct(BaseModel):
    """Israeli grocery product model."""
    ItemCode: str
    ItemName: str
    ManufacturerName: str
    ItemPrice: float
    Quantity: str
    UnitOfMeasure: str
    bIsWeighted: str
    ManufacturerItemDescription: Optional[str] = None
    ChainAlias: str
    ItemId: str


class MatchResult(BaseModel):
    """Result of product matching."""
    matched_product: GroceryProduct
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    similarity_score: float
    text_similarity: Optional[float] = None
    manufacturer_match: Optional[bool] = None
    price_difference_percent: Optional[float] = None


class ProductDatabase:
    """Product database with retrieval capabilities."""

    def __init__(self, products: list[dict]):
        self.products = products
        self.n_products = len(products)

        print(f"Building indexes for {self.n_products} products...")
        self._build_manufacturer_index()
        self._build_tfidf_index()
        self._parse_quantities()
        print("Database ready!")

    def _build_manufacturer_index(self):
        """Index by manufacturer."""
        self.manufacturer_index = {}
        for idx, p in enumerate(self.products):
            mfr = mfr = (
            p.get('ManufacturerName') or
            p.get('manufacturer_name') or
            p.get('Manufacturer') or
            p.get('brand') or
            p.get('Brand') or
            p.get('BrandName') or
            ''
        ).strip()
            if mfr and mfr not in ['לא ידוע', '', 'unknown']:
                if mfr not in self.manufacturer_index:
                    self.manufacturer_index[mfr] = []
                self.manufacturer_index[mfr].append(idx)
        print(f"  ✓ {len(self.manufacturer_index)} manufacturers indexed")

    def _build_tfidf_index(self):
        """Build TF-IDF index for text similarity."""
        self.search_texts = []
        for p in self.products:
            text_parts = [
                p.get('ItemName', ''),
                p.get('ManufacturerItemDescription', ''),
                p.get('ManufacturerName', ''),
            ]
            combined = ' '.join(filter(None, text_parts))
            self.search_texts.append(combined)

        self.vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(3, 5),
            min_df=2,
            max_df=0.85,
            lowercase=True
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(self.search_texts)
        print(f"  ✓ TF-IDF index built: {self.tfidf_matrix.shape}")

    def _parse_quantities(self):
        """Parse quantity values."""
        self.quantity_values = []
        for p in self.products:
            qty_str = p.get('Quantity', '1.00')
            try:
                qty = float(qty_str)
            except (ValueError, TypeError):
                qty = 1.0
            self.quantity_values.append(qty)

    def retrieve_candidates(self, product: dict, top_k: int = 15) -> list[dict]:
        """Retrieve top-k most similar products."""

        # Build query
        query_text = ' '.join([
            product.get('ItemName') or product.get('ItemNm'),
            product.get('ManufacturerItemDescription', ''),
            product.get('ManufacturerName', ''),
        ])

        # 1. Text similarity
        query_vec = self.vectorizer.transform([query_text])
        text_similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        # 2. Manufacturer match
        input_manufacturer = (product.get('ManufacturerName') or '').strip()
        manufacturer_scores = np.array([
            1.0 if ((p.get('ManufacturerName') or '').strip() == input_manufacturer
                    and input_manufacturer not in ['לא ידוע', '', 'unknown'])
            else 0.0
            for p in self.products
        ])

        # 3. Weighted match
        input_weighted = product.get('bIsWeighted', '0')
        weighted_scores = np.array([
            1.0 if p.get('bIsWeighted', '0') == input_weighted else 0.5
            for p in self.products
        ])

        # 4. Quantity similarity
        input_qty = float(product.get('Quantity', '1.00'))
        qty_scores = np.zeros(self.n_products)
        for idx, qty_val in enumerate(self.quantity_values):
            if qty_val > 0 and input_qty > 0:
                diff = abs(input_qty - qty_val) / max(input_qty, qty_val)
                if diff <= 0.5:
                    qty_scores[idx] = 1 - (diff / 0.5)

        # 5. Price similarity
        input_price = float(product.get('ItemPrice', 0))
        price_scores = np.zeros(self.n_products)
        if input_price > 0:
            for idx, p in enumerate(self.products):
                p_price = float(p.get('ItemPrice', 0))
                if p_price > 0:
                    diff = abs(input_price - p_price) / input_price
                    if diff <= 0.3:
                        price_scores[idx] = 1 - (diff / 0.3)

        # Combine scores
        if manufacturer_scores.sum() > 0:
            combined_scores = (
                    0.40 * text_similarities +
                    0.35 * manufacturer_scores +
                    0.10 * weighted_scores +
                    0.10 * qty_scores +
                    0.05 * price_scores
            )
        else:
            combined_scores = (
                    0.50 * text_similarities +
                    0.20 * manufacturer_scores +
                    0.15 * weighted_scores +
                    0.10 * qty_scores +
                    0.05 * price_scores
            )

        # Get top-k
        top_indices = np.argsort(combined_scores)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            product_copy = self.products[idx].copy()
            product_copy['_similarity'] = float(combined_scores[idx])
            product_copy['_text_sim'] = float(text_similarities[idx])
            product_copy['_mfr_match'] = bool(manufacturer_scores[idx])
            results.append(product_copy)

        return results


class ProductMatcher:
    """
    Main class for product matching using AI agent.
    """

    def __init__(self, products: list[dict], ):
        """
        Initialize the matcher.

        Args:
            products: List of product dictionaries
            model: AI model to use ('openai:gpt-4o', 'anthropic:claude-sonnet-4', etc.)
        """
        self.db = ProductDatabase(products)

    async def find_match(
            self,
            input_product: dict,
            top_k: int = 15,
            verbose: bool = True
    ) -> list[dict]:
        """
        Find the best matching product.

        Args:
            input_product: Product to match
            top_k: Number of candidates to retrieve
            verbose: Print progress information

        Returns:
            MatchResult with match details
        """

        if verbose:
            print(f"\n{'=' * 70}")
            print(f"Searching: {(input_product.get('ItemName') or input_product.get('ItemNm') or '')[:50]}")
            print(f"{'=' * 70}")

        # Step 1: Retrieve candidates
        candidates = self.db.retrieve_candidates(input_product, top_k=top_k)

        if verbose:
            print(f"\nTop {min(5, len(candidates))} candidates:")
            try:
                for i, c in enumerate(candidates[:5], 1):
                    print(f"{i}. {(c.get('ItemName') or c.get('ItemNm', ''))[:40]} | {c['ManufacturerName'][:20]} | "
                          f"₪{c['ItemPrice']} | {c['ItemCode']} | sim={c.get('_similarity', 0):.3f}")
            except Exception:
                pass
        # Number of candidates to return
        n = min(5, len(candidates))
        return candidates[:n]

    async def batch_match(
            self,
            input_products: list[dict],
            batch_size: int = 10,
            min_confidence: float = 0.6
    ) -> dict:
        """
        Match multiple products in batches.

        Args:
            input_products: List of products to match
            batch_size: Number of products to process concurrently
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary with results and statistics
        """
        import asyncio

        all_results = []
        high_confidence = []
        low_confidence = []

        total = len(input_products)

        for i in range(0, total, batch_size):
            batch = input_products[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            # print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} products)...")

            # Process batch concurrently
            tasks = [self.find_match(p, verbose=False) for p in batch]
            batch_results = await asyncio.gather(*tasks)

            all_results.extend(batch_results)

            # Categorize results
            for result in batch_results:
                if result.confidence >= min_confidence:
                    high_confidence.append(result)
                else:
                    low_confidence.append(result)

            # print(
            #     f"  Batch complete. High confidence: {len([r for r in batch_results if r.confidence >= min_confidence])}/{len(batch)}")

        return {
            'all_results': all_results,
            'high_confidence': high_confidence,
            'low_confidence': low_confidence,
            'stats': {
                'total': len(all_results),
                'high_confidence_count': len(high_confidence),
                'low_confidence_count': len(low_confidence),
                'high_confidence_rate': len(high_confidence) / len(all_results) if all_results else 0,
                'avg_confidence': np.mean([r.confidence for r in all_results]) if all_results else 0
            }
        }


async def get_alternatives(all_products: list[dict], input_product):
    # Initialize matcher (one time setup)
    print("Initializing matcher...")
    matcher = ProductMatcher(all_products, )

    # Example 1: Match a single product
    result = await matcher.find_match(input_product, top_k=TOP_K_CANDIDATES)

    # print(result)
    return result

