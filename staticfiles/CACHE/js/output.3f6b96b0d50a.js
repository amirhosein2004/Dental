document.addEventListener("DOMContentLoaded",function(){let loadMoreButton=document.getElementById("load-more");let filterForm=document.getElementById("blogFilterForm");let noMoreBlogs=document.getElementById("no-more-blogs");if(loadMoreButton){loadMoreButton.addEventListener("click",function(){let offset=parseInt(this.getAttribute("data-offset"))||0;let formData=new FormData(filterForm);let queryParams=new URLSearchParams(formData);queryParams.set("offset",offset);fetch(`${loadMoreButton.getAttribute("data-url")}?${queryParams.toString()}`,{method:"GET",headers:{"X-Requested-With":"XMLHttpRequest"}}).then(response=>{if(!response.ok){console.error("خطا در پاسخ سرور:",response.status);throw new Error("خطای سرور");}
return response.json();}).then(data=>{console.log("داده‌های دریافتی:",data);let container=document.getElementById("blog-container");if(data.blogs&&data.blogs.length>0){data.blogs.forEach(blog=>{let div=document.createElement("div");div.classList.add("col-12","col-sm-6","col-md-4","col-lg-4");div.innerHTML=`
                            <article class="blog-card" itemscope itemtype="http://schema.org/BlogPosting">
                                <a href="/blog/detail/${blog.slug}/" class="stretched-link" aria-label="مشاهده مقاله: ${blog.title}"></a>
                                <div class="card-content">
                                    <div class="card-img-wrapper position-relative overflow-hidden">
                                        <img 
                                            src="${blog.image}" 
                                            class="card-img-top object-fit-cover" 
                                            alt="${blog.title || 'تصویر مقاله'}" 
                                            loading="lazy" 
                                            decoding="async"
                                            itemprop="image">
                                        <div class="img-overlay position-absolute w-100 h-100 top-0 start-0"></div>
                                    </div>
                                    <div class="card-body p-4 d-flex flex-column gap-3">
                                        <div class="categories mb-2 d-flex flex-wrap gap-2">
                                            ${blog.categories.length > 0 ? blog.categories.map(category => `<span class="badge badge-category"itemprop="keywords">${category}</span>`).join('') : '<span class="badge badge-category text-muted">بدون دسته‌بندی</span>'}
                                        </div>
                                        <h3 class="h5 fw-bold mb-0 line-clamp-2" itemprop="headline">${blog.title}</h3>
                                        <div class="d-flex align-items-center justify-content-between mt-auto">
                                            <div class="author-info" itemprop="author" itemscope itemtype="http://schema.org/Person">
                                                <span class="fw-semibold" itemprop="name">${blog.writer || 'ناشناس'}</span>
                                            </div>
                                            <a href="/blog/detail/${blog.slug}/" 
                                               class="btn btn-link text-primary fw-medium" 
                                               aria-label="مشاهده مقاله: ${blog.title}">
                                                ادامه مطلب <i class="fas fa-arrow-left ms-2" aria-hidden="true"></i>
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </article>
                        `;container.appendChild(div);});loadMoreButton.setAttribute("data-offset",offset+data.blogs.length);if(noMoreBlogs){noMoreBlogs.style.display="none";}}else{console.log("هیچ بلاگی برای نمایش نیست.");if(noMoreBlogs){noMoreBlogs.style.display="block";}
loadMoreButton.style.display="none";}
if(!data.has_more){loadMoreButton.style.display="none";if(noMoreBlogs){noMoreBlogs.style.display="block";}}}).catch(error=>console.error("خطا:",error));});}});;