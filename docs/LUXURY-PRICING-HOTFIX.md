# HOTFIX — Luxury pricing without sale/strikethrough prices

Owner decision: product prices use one luxury retail price only. WooCommerce sale prices, discount badges and strikethrough regular prices are prohibited.

## Enforced code policy

- `regular_price` always equals the final selected/computed Toman price.
- Excel COL 10 remains trace metadata only and cannot affect storefront pricing.
- Importers and the pricing engine never set a sale-price field.
- Whenever existing product pricing is written, stale `_sale_price`/sale-date metadata is deleted and `_price` is synchronized with `_regular_price`.

## PR-34 exact pricing policy

```text
legacy_price = exact current Excel price in Toman
computed_floor = verified weight × approved gram rate, when weight exists
selected_price = max(legacy_price, computed_floor)
final_price = ceil(selected_price to the next whole Toman only)
```

There is no 50000-Toman rounding and no automatic 9-ending/charm pricing. Missing weight uses the exact Excel price with `pricing_mode=legacy_mirror`. The exact values and selection reason are saved in `radman_legacy_price_exact_toman`, `radman_computed_floor_exact_toman`, `radman_final_price_exact_toman`, `radman_price_rounding_policy`, and `radman_price_selection_reason`.

Guarded preview/apply commands are documented in `docs/PRODUCT-SEO-AND-AI-VISIBILITY-RUNBOOK.md`.

## One-time cleanup for the 20 existing Drafts

Create a database backup, then run this exact WP-CLI command on staging. It targets at most 20 Draft products with `legacy_product_id`, newest ID first. If an old sale price exists, the currently effective `_price` is preserved as the final luxury price, copied to `_regular_price`, then `_sale_price` is deleted and `_price` is synchronized.

```bash
wp --path=/home/radmansi/staging.radmansilver.ir --no-color eval '
$q = new WP_Query(array(
  "post_type"      => "product",
  "post_status"    => "draft",
  "posts_per_page" => 20,
  "fields"         => "ids",
  "meta_key"       => "legacy_product_id",
  "orderby"        => "meta_value_num",
  "order"          => "DESC",
));
$updated = array();
foreach ($q->posts as $id) {
  $regular  = (string) get_post_meta($id, "_regular_price", true);
  $effective = (string) get_post_meta($id, "_price", true);
  $sale     = (string) get_post_meta($id, "_sale_price", true);
  if ($sale !== "" && $effective !== "") {
    $regular = $effective;
    update_post_meta($id, "_regular_price", $regular);
  }
  delete_post_meta($id, "_sale_price");
  update_post_meta($id, "_price", $regular);
  wc_delete_product_transients($id);
  $updated[] = array(
    "id"            => (int) $id,
    "regular_price" => $regular,
    "sale_removed"  => true,
  );
}
echo wp_json_encode(array("count" => count($updated), "products" => $updated));
'
```

## Read-only verification

```bash
wp --path=/home/radmansi/staging.radmansilver.ir --no-color eval '
$q = new WP_Query(array(
  "post_type"      => "product",
  "post_status"    => "draft",
  "posts_per_page" => 20,
  "fields"         => "ids",
  "meta_key"       => "legacy_product_id",
  "orderby"        => "meta_value_num",
  "order"          => "DESC",
));
$out = array();
foreach ($q->posts as $id) {
  $out[] = array(
    "id"      => (int) $id,
    "regular" => (string) get_post_meta($id, "_regular_price", true),
    "price"   => (string) get_post_meta($id, "_price", true),
    "sale"    => (string) get_post_meta($id, "_sale_price", true),
  );
}
echo wp_json_encode($out);
'
```

Expected for every row: `regular == price` and `sale == ""`.
