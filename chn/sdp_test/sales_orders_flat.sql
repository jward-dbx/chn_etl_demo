-- Flat sales order table joining order details with product information
-- Note: Table name only (no schema prefix) because target schema is set in pipeline config
CREATE OR REFRESH STREAMING TABLE sales_orders_flat
AS SELECT 
  -- Sales Order Detail fields
  sod.SalesOrderID,
  sod.SalesOrderDetailID,
  sod.OrderQty,
  sod.UnitPrice,
  sod.UnitPriceDiscount,
  sod.LineTotal,
  sod.ModifiedDate as OrderModifiedDate,
  
  -- Product fields
  p.ProductID,
  p.Name as ProductName,
  p.ProductNumber,
  p.Color as ProductColor,
  p.StandardCost,
  p.ListPrice,
  p.Size as ProductSize,
  p.Weight as ProductWeight,
  p.ProductCategoryID,
  p.ProductModelID,
  p.SellStartDate,
  p.SellEndDate,
  p.DiscontinuedDate,
  
  -- Calculated fields
  sod.OrderQty * sod.UnitPrice as ExtendedPrice,
  (sod.OrderQty * sod.UnitPrice) - sod.LineTotal as TotalDiscount

FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.salesorderdetail) sod
INNER JOIN STREAM(dbx_chn_ward_demo.landing_ss_aw.product) p
  ON sod.ProductID = p.ProductID
